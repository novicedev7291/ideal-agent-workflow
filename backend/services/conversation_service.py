from datetime import datetime
from typing import Any, Dict, List, Optional
from uuid import uuid4
from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, text, select
from app.core.exceptions import ConversationException
from app.core.logging import get_logger
from app.core.pg import pg_engine

from sqlalchemy.orm import Session, DeclarativeBase, relationship, mapped_column, Mapped

logger = get_logger(__name__)

class BaseModel(DeclarativeBase):
    pass


class Conversation(BaseModel):
    __tablename__ = 'conversations'
    id = Column(String)
    session_id = Column(String)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)
    metadata_field = Column(name='metadata', type=JSON)
    messages: Mapped[List['Message']] = relationship(back_populates="conversation")


class Message(BaseModel):
    __tablename__ = 'messages'
    id = Column(Integer)
    conversation_id = mapped_column(ForeignKey('conversations.id'))
    conversation: Mapped['Conversation'] = relationship(back_populates="messages") 
    role = Column(String)
    content = Column(String)
    metadata = Column(JSON)
    created_at = Column(DateTime)


class ConversationService:
    def __init__(self):
        self.__initialize_db()

    def __initialize_db(self):
        with Session(pg_engine) as session:
            session.begin()
            try:
                session.execute(text(
                    '''
                    create table if not exists conversations (
                        id uuid primary key,
                        session_id varchar(255) unique not null,
                        created_at timestamp default current_timestamp,
                        updated_at timestamp default current_timestamp,
                        metadata jsonb
                    )
                    '''
                ))

                session.execute(text(
                    '''
                    create table if not exists messages (
                        id serial primary key,
                        conversation_id uuid references conversations(id) on delete cascade,
                        role varchar(50) not null,
                        content text not null,
                        metadata jsonb,
                        created_at timestamp default current_timestamp
                    )
                    '''
                ))

                session.execute(text(
                    '''
                    create index if not exists idx_messages_conversation
                    on messages(conversation_id, created_at)
                    '''
                ))

                session.commit()
            except Exception as e:
                session.rollback()
                raise e

    
    def create_conversation(self, session_id: Optional[str] = None) -> str:
        conversation_id = str(uuid4())

        if not session_id:
            session_id = conversation_id

        with Session(pg_engine) as session:
            try:
                session.add(Conversation(
                    id=conversation_id,
                    session_id=session_id
                ))
            except Exception as e:
                raise e

        return conversation_id

    def get_conversation_by(self, session_id: str) -> List[Conversation]:
        with Session(pg_engine) as session:
            try:
                return session.scalars(select(Conversation).where(Conversation.session_id.is_(session_id)))
            except Exception as e:
                logger.error(f'Exception occurred fetching conversation by session_id {session_id}', e)
            return []
            
    def add_message(self, conv_id: str, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        with Session(pg_engine) as session:
            session.begin()
            try:
                results: List[Conversation] = session.scalars(select(Conversation).where(Conversation.id.is_(conv_id)).limit(1))
                
                conversation = results[0]

                message = Message(
                    conversation_id=conv_id,
                    role=role,
                    content=content,
                    metadata=metadata
                )

                conversation.messages.append(message)
                conversation.updated_at = datetime.now(datetime.tzname())

                session.commit()
            except Exception as e:
                session.rollback()
                raise e

    def get_conv_history(self, conv_id: str) -> List[Message]:
        with Session(pg_engine) as session:
            try:
                results: List[Message] = session.scalars(select(Message).where(Message.conversation_id.is_(conv_id)).order_by(Message.created_at))
                return results
            except Exception as e:
                logger.error(f'Exception occurred while fetching conversation {conv_id} history', e)
            return []

    
