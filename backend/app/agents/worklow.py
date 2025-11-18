import base64
from io import BytesIO
import json
from pathlib import Path
from typing import Optional, TypedDict, List, Annotated, AsyncIterator
from pydantic import BaseModel, Field, ValidationError

from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from google import genai

from PIL import Image

from app.agents.state_manager import AgentState, SearchResult, StateManager
from app.agents.tools.knowledgebase import KnowledgeBase, Screen
from app.core.logging import get_logger
from app.core.config import config

logger = get_logger(__name__)


class IntentSchema(BaseModel):
    task: str = Field(description="The task user wants agent to perform")
    screen: str = Field(description="The screen on which user want to perform the task")
    application: str = Field(description="The application for which screen needs to be changed/added")
    error: Optional[str] = None

class FeedbackSchema(BaseModel):
    yes_no: bool = Field(description='Whether to proceed or not', default=False)
    refined_query: Optional[str] = Field(description='Any refined input provided to be considered')


class AgentWorklow:
    def __init__(self, kb: KnowledgeBase, state_manager: StateManager):
        self.kb = kb
        self.sm = state_manager

        self.general_llm = ChatOpenAI(
            model="gpt-4o-mini",
            api_key=lambda: config.OPEN_AI_KEY if config.OPEN_AI_KEY else 'default-value',
            streaming=True,
            temperature=0.7
        )

        self.image_llm = genai.Client(
            api_key=config.GOOGLE_AI_KEY
        )

        self.workflow = None
        self._initialize()

    def _initialize(self):
        """Initialize langgraph workflow to be used over chat API"""
        workflow = StateGraph(AgentState)
        
        workflow.add_node("analyze_intent", self._analyze_intent_node)
        workflow.add_node("search_knowledge_base", self._search_kb_node)
        workflow.add_node("summarise_view", self._summarise_view)
        workflow.add_node("edit_image", self._edit_image_node)
        workflow.add_node("generate_response", self._generate_response_node)
        workflow.add_node("send_response", self._send_response_node)
        workflow.add_node("feedback_loop", self._feedback_loop_node)
        
        workflow.set_entry_point("analyze_intent")
        
        workflow.add_conditional_edges(
            "analyze_intent",
            self._route_after_intent
        )

        workflow.add_conditional_edges(
            "feedback_loop",
            self._route_after_feedback
        )
        
        workflow.add_edge("search_knowledge_base", "summarise_view")
        workflow.add_edge("summarise_view", "edit_image")
        workflow.add_edge("edit_image", "generate_response")
        workflow.add_edge("generate_response", "send_response")
        workflow.add_edge("send_response", END)
        
        self.workflow = workflow.compile()
        logger.info("LangGraph workflow initialized successfully")

    
    def _summarise_view(self, state: AgentState) -> AgentState:
        logger.debug('Inside _summarise_view')
        try:
            context = self._build_kb_context(state.get('search_results'))
            system_prompt = f"""You are summary assistance.
Given is the elaborative screen context about description, features etc.

Screen Context:
{context}

"""
            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content='Provide a summary under 300 words to describe the screen')
            ]
            response = self.general_llm.invoke(messages)

            state['view_summary'] = response.content

        except Exception as e:
            logger.error('Error occurred while summarising the screen : ', e)
        
        return state

    
    def _route_after_feedback(self, state: AgentState) -> str:
        if state['error']:
            return 'generate_response'

        if state['redo_edit']:
            return 'edit_image'

        return 'generate_response'


    def _feedback_loop_node(self, state: AgentState) -> AgentState:
        try:
            # Since, must have reached here only when user feedback is already asked!
            state['need_user_clarification'] = False

            user_input = state.get('user_input')

            system_instructions = """You are a query analyser assistant.

Return your response as a valid JSON object with these exact fields:
- yes_no: User has provided yes or no answer, boolean field.
- refined_query: Any query additonally user has provided to process further, string field.
"""
            instructions = [
                SystemMessage(content=system_instructions),
                HumanMessage(content=user_input)
            ]

            resp = self.general_llm.invoke(instructions)

            try:
                feedback_dict = json.loads(resp.content)

                feedback = FeedbackSchema(**feedback_dict)

                if not feedback.yes_no:
                    state['redo_edit'] = True
                    state['edited_img'] = None

                if feedback.refined_query:
                    state['task'] = feedback.refined_query

                state['agent_query'] = None
                state['messages'].append({'role': 'user', 'content': user_input})

                return state
            except Exception as ex:
                logger.error('Error occurred while parsing feedback', ex)
                state['error'] = str(ex)
        except Exception as e:
            logger.error('Error occurred while providing feedback', e)
            state['error'] = str(e)
        return state


    def _edit_image_node(self, state:  AgentState) -> AgentState:
        logger.debug('Inside _edit_image_node')
        try:
            view_summary = state['view_summary']
            
            prompts = (
                view_summary,
                state.get('task')
            )

            root_folder = Path(__file__).parent.parent.parent

            original_image_path = state['original_img']
            image_name = original_image_path.split('/')[2]
            image = Image.open(state['original_img'])

            resp = self.image_llm.models.generate_content(
                model='gemini-2.5-flash-image',
                contents=[prompts, image],
            )

            edited_img_path =f'data/edited/{image_name}'

            final_location = str(root_folder / edited_img_path)

            logger.debug(f'Edited image is being saved to folder : {final_location}')

            for part in resp.parts:
                if part.inline_data is not None:
                    image_mime = part.inline_data.mime_type
                    image_part = part.as_image()
                    image_part.save(final_location)
                    
                    state['edited_img'] = final_location
                    state['image_mime'] = image_mime
                    state['need_user_clarification'] = True

            state['redo_edit'] = False
        except Exception as e:
            logger.error('Error while editing image', e)

        return state

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
            if state.get('need_user_clarification'):
                    return state
            
            try:
                state['task'] = state['user_input']
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
        if state.get('need_user_clarification'):
            return 'feedback_loop'
        return 'search_knowledge_base'

    def _search_kb_node(self, state: AgentState) -> AgentState:
        logger.info(f"Searching knowledge base for task: {state['task']}")
        
        try:
            search_query = f"{state['task']}"
            
            results = self.kb.search_screens(search_query)
            
            state['search_results'] = [SearchResult(content=s.content, img_urls=[img.url for img in s.imgs]) for s in results]

            # TODO: Check how to pick multiple results instead of 1
            state['original_img'] = results[0].imgs[0].url
            logger.info(f"Found {len(results)} relevant screens in knowledge base")
            
        except Exception as e:
            logger.error(f"Error searching knowledge base: {e}")
            state['search_results'] = []
        
        return state

    def _generate_response_node(self, state: AgentState) -> AgentState:
        logger.info("Generating response with LLM")

        if state.get('need_user_clarification'):
            state['agent_query'] = 'Below is the modified screen as per your query, do you want me to proceed with the changes?'
        else:
            state['agent_query'] = None

        return state

    def _send_response_node(self, state: AgentState) -> AgentState:
        logger.debug(f'Inside _send_response_node with state {state}')

        if state.get('error'):
            logger.info(f"Sending error response: error not inferred")
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
            'task': state.get('task'),
            'summary': state.get('summary'),
            'search_results': state.get('search_results'),
            'messages': state.get('messages'),
            'edited_img': state.get('edited_img'),
            'original_img': state.get('original_img'),
            'view_summary': state.get('view_summary'),
            'image_mime': state.get('image_mime'),
            'need_user_clarification': state.get('need_user_clarification'),
            'error': None, # Reset error every time
            'agent_query': state.get('agent_query'),
            'redo_edit': state.get('redo_edit')
        }
        
        try:
            full_response = []
            current_state = None

            async for event in self.workflow.astream(workflow_state):
                node_name = list(event.keys())[0]
                node_state: AgentState = event[node_name]
                current_state = node_state

                if node_name == 'generate_response':
                    async for token in self._stream_generate_response(node_state):
                        logger.debug(f'returning token : {token}')
                        full_response.append(token)

                        yield token

                if node_state.get('error'):
                    yield f"\nError: {node_state['error']}"
                    return

            logger.debug(f'Current state : {current_state is not None}')
            if current_state:
                state['messages'].append({'role': 'user', 'content': user_input})
                assistant_msgs = [json.loads(r) for r in full_response]

                if assistant_msgs:
                    for m in assistant_msgs:
                        if m.get('mime') == 'image/png':
                            m['content'] = '[image-data-noout]'
                    
                    state['messages'].append({'role': 'assistant', 'content': '\n'.join([m['content'] for m in assistant_msgs])})

                state['task'] = current_state.get('task', '')
                state['search_results'] = [s for s in current_state.get('search_results', [])]
                state['user_input'] = current_state.get('user_input')
                state['edited_img'] = current_state.get('edited_img')
                state['original_img'] = current_state.get('original_img')
                state['image_mime'] = current_state.get('image_mime')
                state['view_summary'] = current_state.get('view_summary')
                state['need_user_clarification'] = current_state.get('need_user_clarification')
                state['error'] = current_state.get('error')
                state['redo_edit'] = current_state.get('redo_edit')

                self.sm.update_state(session_id, state)

        except Exception as e:
            logger.error(f"Error in streaming message processing: {e}")
            yield f"\n\nError: {str(e)}"

    def _image_to_base64_with_details(self, img_loc: str) -> dict:
        try:
            root_folder = Path(__file__).parent.parent.parent

            with Image.open(root_folder / img_loc) as img:
                bufferred = BytesIO()
                img.save(bufferred, format=img.format or 'PNG')
                img_bytes = bufferred.getvalue()

                img_base64 = base64.b64encode(img_bytes).decode('utf-8')

                return {
                    'content': img_base64,
                    'mime_type': f'image/{(img.format or 'png').lower()}',
                    'height': img.width,
                    'width': img.width,
                }

        except Exception as e:
            raise e

    async def _stream_generate_response(self, state: AgentState) -> AsyncIterator[str]:
        """
        Stream response generation using LLM
        """
        logger.debug('Inside _stream_generate_response')

        if state.get('edited_img') and state.get('need_user_clarification'):
            try:
                yield json.dumps({"content": state.get('agent_query'), "mime": "text/plain"})
                img_loc = state.get('edited_img')
                img_b64_details = self._image_to_base64_with_details(img_loc)
                yield json.dumps({"content": img_b64_details.get('content'), "mime": img_b64_details.get('mime_type')})
            except Exception as e:
                yield json.dumps({"content": f"Error generating response: {str(e)}", "mime": "text/plain"})
            
            return
        else:
            kb_context = self._build_kb_context(state['search_results'])

            conversations = '\n'.join([f'{m["role"]} : {m["content"]}' for m in state.get('messages')])
            
            system_prompt = f"""You are an AI assistant helping with screen and application management.

Knowledge Base Context:
{kb_context}

Conversation History:
{conversations}

Based on the user's task and the relevant information from the knowledge base, provide a helpful and detailed response.
Suggest specific changes or improvements that align with the user's requirements. Also, check conversation history while providing suggestions."""

            messages = [
                SystemMessage(content=system_prompt),
                HumanMessage(content=state['task'])
            ]
        
            try:
                async for chunk in self.general_llm.astream(messages):
                    if hasattr(chunk, 'content') and chunk.content:
                        yield json.dumps({"content": chunk.content, "mime": "text/plain"})
                        
                logger.debug('Completed _stream_generate_response')
            except Exception as e:
                logger.error(f"Error streaming from OpenAI: {e}")
                yield json.dumps({"content": f"Error generating response: {str(e)}", "mime": "text/plain"})


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
        
        response = self.general_llm.invoke(messages)

        logger.debug('_generate_final_response completed...')
        return response.content

    def _build_kb_context(self, kb_results: List[SearchResult]) -> str:
        """Build formatted context from knowledge base results"""
        if not kb_results:
            return "No relevant screens found in the knowledge base."
        
        context_parts = []

        # TODO: Hardcoding top result for now, have to check what else can be done here?
        result = kb_results[0]
            
        context_parts.append(result.get('content'))
        
        logger.debug('_build_kb_context successfully processed')
        return "\n".join(context_parts)