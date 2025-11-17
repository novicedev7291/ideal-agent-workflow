from datetime import datetime, timedelta
import threading

from typing import Dict, Optional, Tuple, List, TypedDict
from uuid import uuid4

from app.core.logging import get_logger

logger = get_logger(__name__)

class SearchResult(TypedDict):
    content: str
    img_urls: List[str]

class Message(TypedDict):
    role: str
    content: str

class AgentState(TypedDict):
    search_results: List[SearchResult]
    messages: List[Message]
    task: str
    summary: str
    user_input: str
    view_summary: Optional[str]
    original_img: str
    edited_img: Optional[str]
    image_mime: Optional[str]
    need_user_clarification: bool 
    error: Optional[str]
    agent_query: Optional[str]
    redo_edit: bool

class StateManager:
    def __init__(self, ttl: int = 30):
        self._states: Dict[str, Tuple[AgentState, datetime]] = {}
        self._lock = threading.Lock()
        self.ttl = timedelta(minutes=ttl)

    def create_session(self) -> str:
        session_id = str(uuid4())

        with self._lock:
            self._states[session_id] = (AgentState(search_results = [], messages = [], task='', summary=''), datetime.now())

        return session_id

    def get_state(self, session_id: str) -> Optional[AgentState]:
        with self._lock:
            if session_id in self._states:
                state, timestamp = self._states.get(session_id)
                if datetime.now() - timestamp < self.ttl:
                    return state
                else:
                    del self._states[session_id]

        return None


    def update_state(self, session_id: str, n_state: AgentState):
        logger.info(f'Updating session_id {session_id} with {n_state.get('messages') is not None}')
        with self._lock:
            self._states[session_id] = (n_state, datetime.now())


    def clear_expired(self):
        with self._lock:
            expired = [sid for sid, (_, ttl) in self._states.items() if datetime.now() - ttl >= self.ttl]

            for sid in expired:
                del self._states[sid]