import json
from typing import Optional, TypedDict, List, Annotated, AsyncIterator
from pydantic import BaseModel, Field, ValidationError

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage

from app.agents.state_manager import AgentState, StateManager
from app.agents.tools.knowledgebase import KnowledgeBase, Screen
from app.core.logging import get_logger
from app.core.config import config

logger = get_logger(__name__)


class IntentSchema(BaseModel):
    task: str = Field(description="The task user wants agent to perform")
    screen: str = Field(description="The screen on which user want to perform the task")
    application: str = Field(description="The application for which screen needs to be changed/added")
    error: Optional[str] = None


class AgentWorklow:
    def __init__(self, kb: KnowledgeBase, state_manager: StateManager):
        self.kb = kb
        self.sm = state_manager
        self.llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=config.OPEN_AI_KEY,
            streaming=True,
            temperature=0.7
        )
        self.workflow = None
        self._initialize()

    def _initialize(self):
        """Initialize langgraph workflow to be used over chat API"""
        workflow = StateGraph(AgentState)
        
        workflow.add_node("analyze_intent", self._analyze_intent_node)
        workflow.add_node("search_knowledge_base", self._search_kb_node)
        workflow.add_node("generate_response", self._generate_response_node)
        workflow.add_node("send_response", self._send_response_node)
        
        workflow.set_entry_point("analyze_intent")
        
        workflow.add_conditional_edges(
            "analyze_intent",
            self._route_after_intent
        )
        
        workflow.add_edge("search_knowledge_base", "generate_response")
        workflow.add_edge("generate_response", "send_response")
        workflow.add_edge("send_response", END)
        
        self.workflow = workflow.compile()
        logger.info("LangGraph workflow initialized successfully")


    def _analyze_intent_node(self, state: AgentState) -> AgentState:
        try:
            system_prompt = """You are an intent extraction assistant. 
Extract the task, screen, and application from the user's request.

Return your response as a valid JSON object with these exact fields:
- task: The task user wants to perform
- screen: The screen name or identifier
- application: The application name

If any information is missing or unclear, make a reasonable inference based on context.
"""
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=state['user_input'])
            ]
            
            # TODO: Uncomment this here.
            #response = self.llm.invoke(messages)
            response = {
                'task': 'Add a button to view product uploaded image',
                'screen': 'Product Page',
                'application': 'Order Management System'
            }

            logger.debug(f'LLM response : {response}')
            
            try:
                #intent_data = json.loads(response)
                intent = IntentSchema(**response)
                
                state['task'] = intent.task
                state['screen'] = intent.screen
                state['application'] = intent.application
                
                logger.info(f"Intent extracted: task={intent.task}, screen={intent.screen}, app={intent.application}")
                
            except (json.JSONDecodeError, ValidationError) as e:
                logger.warning(f"Failed to parse intent: {e}")
                state['error'] = "Could not understand the request. Please provide task, screen, and application details."
                
        except Exception as e:
            logger.error(f"Error in intent analysis: {e}")
            state['error'] = f"Error analyzing intent: {str(e)}"
        
        return state

    def _route_after_intent(self, state: AgentState) -> str:
        logger.debug(f'Inside _route_after_intent with state : {state}')
        if state.get('error'):
            return 'send_response'
        return 'search_knowledge_base'

    def _search_kb_node(self, state: AgentState) -> AgentState:
        logger.info(f"Searching knowledge base for task: {state['task']}")
        
        try:
            search_query = f"{state['task']}"
            
            results = self.kb.search_screens(search_query)
            
            state['search_results'] = [s.content for s in results]
            logger.info(f"Found {len(results)} relevant screens in knowledge base")
            
        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            state['search_results'] = []
            state['error'] = f"Error searching knowledge base: {str(e)}"
        
        return state

    def _generate_response_node(self, state: AgentState) -> AgentState:
        logger.info("Generating response with LLM")
        
        state['response'] = ''
        
        return state

    def _send_response_node(self, state: AgentState) -> AgentState:
        logger.debug(f'Inside _send_response_node with state {state}')

        if state.get('error'):
            logger.info(f"Sending error response: {state['error']}")
        else:
            logger.info("Response prepared successfully")
        
        return state


    def start_session(self) -> str:
        """Create a new session and return session ID"""
        return self.sm.create_session()

    
    def process_message(self, session_id: str, user_input: str) -> str:
        state = self.sm.get_state(session_id)
        
        if not state:
            raise ValueError(f'Session with {session_id} not found')
        
        workflow_state: AgentState = AgentState(**{
            'user_input': user_input,
            'task': '',
            'summary': '',
            'search_results': [],
            'messages': []
        })
        
        try:
            final_state = self.workflow.invoke(workflow_state)
            
            if final_state.get('error'):
                return final_state['error']
            
            response = self._generate_final_response(final_state)
            
            state.messages.append(user_input)
            state.task = final_state.get('task', '')
            state.search_results = [s.name for s in final_state.get('kb_results', [])]
            self.sm.update_state(session_id, state)
            
            return response
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return f"An error occurred: {str(e)}"


    async def stream_process_message(self, session_id: str, user_input: str) -> AsyncIterator[str]:
        """
        Process a message through the workflow with streaming support
        This method yields tokens as they arrive from OpenAI
        """
        state = self.sm.get_state(session_id)
        
        if not state:
            yield "Error: Session not found"
            return
        
        workflow_state: AgentState = {
            'user_input': user_input,
            'task': '',
            'summary': '',
            'search_results': [],
            'messages': []
        }
        
        try:
            full_response = []
            current_state = None

            async for event in self.workflow.astream(workflow_state):
                node_name = list(event.keys())[0]
                node_state = event[node_name]
                current_state = node_state

                if node_name == 'generate_response':
                    async for token in self._stream_generate_response(node_state):
                        full_response.append(token)

                        yield token

                if node_state.get('error'):
                    yield f"\nError: {node_state['error']}"
                    return

            if current_state:
                state['messages'] = []
                state['messages'].append({'role': 'user', 'content': user_input})
                state['messages'].append({'role': 'assistant', 'content': ''.join(full_response)})
                state['task'] = current_state.get('task', '')
                state['search_results'] = [s for s in current_state.get('search_results', [])]
                state['user_input'] = current_state.get('user_input')
                self.sm.update_state(session_id, state)

        except Exception as e:
            logger.error(f"Error in streaming message processing: {e}")
            yield f"\n\nError: {str(e)}"

    async def _stream_generate_response(self, state: AgentState) -> AsyncIterator[str]:
        """
        Stream response generation from OpenAI
        """
        kb_context = self._build_kb_context(state['search_results'])
        
        system_prompt = f"""You are an AI assistant helping with screen and application management.

Knowledge Base Context:
{kb_context}

Based on the user's task and the relevant information from the knowledge base, provide a helpful and detailed response.
Suggest specific changes or improvements that align with the user's requirements."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=state['user_input'])
        ]
        
        try:
            async for chunk in self.llm.astream(messages):
                if hasattr(chunk, 'content') and chunk.content:
                    yield chunk.content
                    
            logger.debug('Completed _stream_generate_response')
        except Exception as e:
            logger.error(f"Error streaming from OpenAI: {e}")
            yield f"\n\nError generating response: {str(e)}"


    def _generate_final_response(self, state: AgentState) -> str:
        """Generate final response using LLM (non-streaming)"""
        logger.debug('Inside _generate_final_response...')
        kb_context = self._build_kb_context(state['search_results'])
        
        system_prompt = f"""You are an AI assistant helping with screen and application management.

Knowledge Base Context:
{kb_context}

Based on the user's task and the relevant information from the knowledge base, provide a helpful and detailed response.
Suggest specific changes or improvements that align with the user's requirements."""

        messages = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=state['user_input'])
        ]
        
        response = self.llm.invoke(messages)

        logger.debug('_generate_final_response completed...')
        return response.content

    def _build_kb_context(self, kb_results: List[Screen]) -> str:
        """Build formatted context from knowledge base results"""
        if not kb_results:
            return "No relevant screens found in the knowledge base."
        
        context_parts = []
        for screen in kb_results:  # Limit to top 3 results
            context_parts.append(screen)
        
        logger.debug('_build_kb_context successfully processed')
        return "\n".join(context_parts)