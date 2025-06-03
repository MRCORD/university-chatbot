# =======================
# app/engines/langgraph/nodes/response_formatting.py - ENHANCED VERSION
# =======================
"""
Response formatting node with intelligent answer generation.

Enhanced node that formats final conversational responses using LLM for document Q&A.
Follows KISS principle but with smart answer synthesis.
"""

import structlog

from app.engines.langgraph.nodes.base_node import BaseNode
from app.engines.langgraph.state.conversation_state import ConversationState, StateManager
from app.engines.langgraph.state.schemas import IntentType

logger = structlog.get_logger()


class ResponseFormattingNode(BaseNode):
    """
    Formats final conversational response with intelligent answer generation.
    
    Enhanced responsibility:
    1. Look at intent and tool results
    2. For document searches: Generate intelligent answers using LLM
    3. For other intents: Format appropriate conversational response
    4. Add suggested actions
    
    This is where the magic happens for document Q&A.
    """
    
    async def execute(self, state: ConversationState) -> ConversationState:
        """
        Format final response with intelligent generation when needed.
        
        Args:
            state: Current conversation state
            
        Returns:
            State updated with formatted response
        """
        self._log_start(state)
        
        try:
            intent = state.get('intent', '')
            tool_result = state.get('tool_result', {})
            tool_success = state.get('tool_success', False)
            sources = state.get('sources', [])
            
            # Route to appropriate response handler
            if intent == IntentType.QUESTION.value:
                response, actions, confidence = await self._format_document_question_response(
                    tool_result, tool_success, sources, state
                )
            elif intent == IntentType.COMPLAINT.value:
                response, actions, confidence = self._format_complaint_response(tool_result, tool_success)
            else:
                response, actions, confidence = await self._format_general_response(state)
            
            # Update state with formatted response
            StateManager.update_response(
                state,
                response=response,
                confidence=confidence,
                suggested_actions=actions
            )
            
            self._log_complete(state)
            return state
            
        except Exception as e:
            error_msg = f"Response formatting failed: {str(e)}"
            self._log_error(state, error_msg)
            
            # Fallback response
            fallback_response = "Lo siento, tuve un problema procesando tu mensaje. ¿Puedes intentar de nuevo?"
            StateManager.update_response(
                state,
                response=fallback_response,
                confidence=0.1,
                suggested_actions=["Intenta reformular tu pregunta"]
            )
            StateManager.add_error(state, "response_formatting_error", error_msg)
            
            return state
    
    async def _format_document_question_response(
        self, 
        tool_result: dict, 
        success: bool, 
        sources: list,
        state: ConversationState
    ) -> tuple:
        """
        Format response for document questions with intelligent answer generation.
        
        Args:
            tool_result: Result from document search tool
            success: Whether document search succeeded
            sources: List of source documents
            state: Current conversation state for user question
            
        Returns:
            Tuple of (response_text, suggested_actions, confidence_score)
        """
        
        if success and tool_result.get('type') == 'document_search':
            # Found relevant documents - generate intelligent answer
            chunks = tool_result.get('chunks', [])
            user_question = tool_result.get('query', state.get('user_message', ''))
            
            if chunks:
                # Use LLM to generate intelligent answer
                answer = await self._generate_intelligent_answer(user_question, chunks)
                
                # Format with sources
                if sources:
                    source_text = ", ".join(sources[:2])  # Max 2 sources for readability
                    response = f"{answer}\n\n📄 Fuente: {source_text}"
                else:
                    response = answer
                
                actions = [
                    "¿Necesitas más detalles sobre este tema?",
                    "¿Hay algo más en lo que pueda ayudarte?"
                ]
                confidence = min(0.9, tool_result.get('best_similarity', 0.7) + 0.1)
                
                return response, actions, confidence
        
        # No documents found or search failed
        response = """No encontré información específica sobre eso en los documentos de UP.

¿Podrías ser más específico o usar palabras clave diferentes? También puedo ayudarte con:
• Procedimientos académicos
• Fechas límite importantes  
• Reglamentos de la universidad"""
        
        actions = [
            "Intenta con palabras clave más específicas",
            "Pregunta sobre un tema específico",
            "Reporta un problema"
        ]
        confidence = 0.3
        
        return response, actions, confidence
    
    async def _generate_intelligent_answer(self, user_question: str, document_chunks: list) -> str:
        """
        Generate answer using ONLY the retrieved documents, no logical leaps.
        """
        try:
            llm_tool = self.tools.get('llm')
            if not llm_tool:
                return self._safe_no_info_response(user_question)
            
            # Prepare context 
            context_parts = []
            for chunk in document_chunks[:3]:
                content = chunk.get('content', '').strip()
                if content:
                    context_parts.append(content)
            
            context_text = "\n\n".join(context_parts)
            
            # Ultra-simple prompt to prevent hallucination
            prompt = f"""¿Los siguientes documentos responden directamente la pregunta \"{user_question}\"?\n\nDocumentos:\n{context_text}\n\nSi SÍ responden directamente: cita la información exacta.\nSi NO responden directamente: responde \"No hay información sobre esto en los documentos.\"\n\nNo interpretes ni deduzcas. Solo información literal.\n\nRespuesta:"""
            
            llm_result = await llm_tool.generate_response(
                prompt=prompt,
                max_tokens=200,
                temperature=0.0  # Zero temperature for consistency
            )
            
            if llm_result.success:
                answer = llm_result.data.get('response', '').strip()
                
                # If LLM says no info, use our standardized message
                if any(phrase in answer.lower() for phrase in ["no hay información", "no encontré", "no responden"]):
                    return self._safe_no_info_response(user_question)
                
                # Otherwise trust the LLM's answer
                return answer
            
            return self._safe_no_info_response(user_question)
                
        except Exception as e:
            return self._safe_no_info_response(user_question)
    
    def _fallback_document_formatting(self, document_chunks: list) -> str:
        """
        Fallback formatting when LLM is not available.
        
        Args:
            document_chunks: List of document chunks
            
        Returns:
            Simple formatted response
        """
        if not document_chunks:
            return "No encontré información relevante en los documentos de UP."
        
        # Take the most relevant chunk and clean it up
        best_chunk = document_chunks[0]
        content = best_chunk.get('content', '')
        
        # Clean up the content
        lines = content.split('\n')
        cleaned_lines = [line.strip() for line in lines if line.strip()]
        cleaned_content = '\n'.join(cleaned_lines[:15])  # First 15 meaningful lines
        
        # Add context
        return f"Según los documentos de UP:\n\n{cleaned_content}"
    
    def _is_likely_hallucination(self, answer: str, question: str, context: str) -> bool:
        """
        Detect potential hallucinations by checking if answer contains 
        specific details not found in context.
        
        Args:
            answer: Generated answer to check
            question: User's original question
            context: Document context provided to the LLM
            
        Returns:
            True if answer likely contains hallucinated content
        """
        # Check for specific numbers/requirements that might be hallucinated
        hallucination_indicators = [
            # Specific grades/scores
            r'\b1[0-9]/20\b',  # Grades like 13/20, 15/20
            r'\b[0-9]+\.[0-9]+\b',  # Decimal numbers
            
            # Specific procedures not in context
            r'examen de admisión',
            r'oficina de admisión',
            r'promedio mínimo',
            r'semestre académico'
        ]
        
        import re
        for pattern in hallucination_indicators:
            if re.search(pattern, answer.lower()) and not re.search(pattern, context.lower()):
                return True
        
        return False
    
    def _safe_no_info_response(self, user_question: str) -> str:
        """Simple fallback when no relevant info found."""
        return f"No encontré información específica sobre '{user_question}' en los documentos disponibles."
        
    def _format_complaint_response(self, tool_result: dict, success: bool) -> tuple:
        """Format response for complaint submissions (unchanged)."""
        
        if success and tool_result.get('type') == 'complaint_submitted':
            short_id = tool_result.get('short_id', 'desconocido')
            response = f"""✅ He registrado tu reporte exitosamente.

📋 ID del reporte: #{short_id}

Tu reporte será revisado por el equipo administrativo. Puedes hacer seguimiento con este ID."""
            
            actions = [
                "¿Hay algo más en lo que pueda ayudarte?",
                "¿Quieres reportar otro problema?"
            ]
            confidence = 0.95
        else:
            response = """Lo siento, no pude registrar tu reporte en este momento.

Por favor intenta de nuevo en unos minutos, o contacta directamente con la administración si es urgente."""
            
            actions = [
                "Intenta reportar de nuevo",
                "Pregunta sobre procedimientos de UP"
            ]
            confidence = 0.2
        
        return response, actions, confidence
    
    async def _format_general_response(self, state: ConversationState) -> tuple:
        """Format response for general conversation (enhanced with LLM)."""
        
        user_message = state.get('user_message', '')
        
        # Try to use LLM for better general responses
        llm_tool = self.tools.get('llm')
        if llm_tool:
            try:
                llm_result = await llm_tool.generate_up_response(user_message)
                if llm_result.success:
                    response = llm_result.data.get('response', '')
                    if response:
                        actions = [
                            "Pregunta sobre procedimientos de UP",
                            "Buscar en documentos oficiales", 
                            "Reportar un problema"
                        ]
                        return response, actions, 0.8
            except Exception as e:
                logger.warning("LLM general response failed", error=str(e))
        
        # Fallback general responses
        if any(greeting in user_message.lower() for greeting in ['hola', 'buenos', 'buenas']):
            response = """¡Hola! Soy el asistente virtual de Universidad del Pacífico.

Puedo ayudarte con:
• Información sobre procedimientos académicos
• Búsqueda en documentos oficiales de UP
• Registro de reportes o problemas

¿En qué puedo ayudarte hoy?"""
            
        elif any(thanks in user_message.lower() for thanks in ['gracias', 'thank']):
            response = """¡De nada! Me alegra haber podido ayudarte.

Si tienes más preguntas sobre UP o necesitas ayuda con algún procedimiento, no dudes en preguntar."""
            
        else:
            response = f"""Vi tu mensaje: "{user_message[:50]}..."

Soy el asistente de Universidad del Pacífico. ¿En qué puedo ayudarte específicamente?"""
        
        actions = [
            "Pregunta sobre procedimientos de UP",
            "Buscar en documentos oficiales", 
            "Reportar un problema"
        ]
        confidence = 0.7
        
        return response, actions, confidence
    
    async def _check_document_relevance(self, question: str, context: str, llm_tool) -> dict:
        """
        First step: Strict relevance checking to prevent hallucination.
        
        Args:
            question: User's question
            context: Document context text
            llm_tool: LLM tool for generation
            
        Returns:
            Dictionary containing relevance result and reason
        """
        
        # Extract key topic from question
        topic_extraction_prompt = f"""Extrae el TEMA ESPECÍFICO de esta pregunta de estudiante:

Pregunta: "{question}"

Responde SOLO con el tema principal en 2-3 palabras. Ejemplos:
- "¿Cuáles son los requisitos para cambiar de carrera?" → "cambio de carrera"
- "¿Cuándo son los exámenes finales?" → "exámenes finales" 
- "¿Cómo me matriculo?" → "matrícula"

Tema específico:"""
        
        topic_result = await llm_tool.generate_response(
            prompt=topic_extraction_prompt,
            max_tokens=10,
            temperature=0.0
        )
        
        if not topic_result.success:
            return {'is_relevant': False, 'reason': 'No se pudo extraer el tema'}
        
        main_topic = topic_result.data.get('response', '').strip().lower()
        
        # Now check if documents contain information about this specific topic
        relevance_prompt = f"""TAREA: Determinar si los documentos contienen información sobre un tema específico.

TEMA BUSCADO: "{main_topic}"

DOCUMENTOS:
{context}

PREGUNTA CRÍTICA: ¿Los documentos contienen información específica y directa sobre "{main_topic}"?

INSTRUCCIONES:
- Responde SOLO "SÍ" o "NO"
- "SÍ" solo si hay información DIRECTA sobre el tema específico
- "NO" si la información es sobre temas relacionados pero diferentes
- "NO" si solo hay menciones tangenciales

EJEMPLOS:
- Si busco "cambio de carrera" pero solo hay info sobre "modificar matrícula" → NO
- Si busco "exámenes finales" y hay fechas de exámenes finales → SÍ
- Si busco "requisitos de admisión" pero solo hay calendario académico → NO

Respuesta (SÍ/NO):"""
        
        relevance_result = await llm_tool.generate_response(
            prompt=relevance_prompt,
            max_tokens=5,
            temperature=0.0
        )
        
        if not relevance_result.success:
            return {'is_relevant': False, 'reason': 'Error en verificación de relevancia'}
        
        relevance_answer = relevance_result.data.get('response', '').strip().upper()
        
        if relevance_answer == "SÍ":
            return {'is_relevant': True, 'main_topic': main_topic}
        else:
            return {
                'is_relevant': False, 
                'reason': f'Los documentos no contienen información específica sobre "{main_topic}"'
            }

    async def _generate_validated_answer(self, question: str, context: str, llm_tool) -> str:
        """
        Second step: Generate answer only when relevance is confirmed.
        
        Args:
            question: User's question
            context: Document context text
            llm_tool: LLM tool for generation
            
        Returns:
            Generated answer from validated context
        """
        
        validated_prompt = f"""Los documentos han sido validados como relevantes para esta pregunta.

PREGUNTA: {question}

DOCUMENTOS RELEVANTES:
{context}

INSTRUCCIONES:
1. Responde usando ÚNICAMENTE la información de los documentos
2. Sé específico y preciso
3. Cita fechas, períodos, o procedimientos exactos si están disponibles
4. Si algo no está claro en los documentos, dilo

Respuesta basada en los documentos:"""
        
        answer_result = await llm_tool.generate_response(
            prompt=validated_prompt,
            max_tokens=250,
            temperature=0.1
        )
        
        if answer_result.success:
            return answer_result.data.get('response', '').strip()
        else:
            return self._safe_no_info_response(question)
    
    def _extract_question_keywords(self, question: str) -> list:
        """
        Extract key terms from the question for validation.
        
        Args:
            question: User's question
            
        Returns:
            List of extracted keywords
        """
        # Simple keyword extraction for validation
        question_lower = question.lower()
        
        key_terms = []
        
        # Academic process keywords
        if 'cambio' in question_lower and 'carrera' in question_lower:
            key_terms.append('cambio de carrera')
        elif 'matricul' in question_lower:
            key_terms.append('matrícula')
        elif 'examen' in question_lower:
            key_terms.append('exámenes')
        elif 'admis' in question_lower:
            key_terms.append('admisión')
        elif 'requisito' in question_lower:
            key_terms.append('requisitos')
        
        return key_terms