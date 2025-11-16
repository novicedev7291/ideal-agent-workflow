import os

from typing import List

from sqlalchemy import ForeignKey, create_engine, Column, Integer, String, JSON, DateTime, select, text
from sqlalchemy.orm import Session, DeclarativeBase, mapped_column, relationship, Mapped, joinedload
from pgvector.sqlalchemy import Vector

from app.core.logging import get_logger
from app.core.pg import pg_engine

logger = get_logger(__name__)


class BaseModel(DeclarativeBase):
    pass

class ScreenModel(BaseModel):
    __tablename__ = 'screens'
    id = Column(Integer, primary_key=True)
    name = Column(String)
    details = Column(String)
    embedding = Column(Vector(1536))
    imgs: Mapped[List['ImageModel']] = relationship(back_populates='screen')
    created_at = Column(DateTime)
    

class ImageModel(BaseModel):
    __tablename__ = 'imgs'
    id = Column(Integer, primary_key=True)
    screen_id = mapped_column(ForeignKey('screens.id'))
    screen: Mapped['ScreenModel'] = relationship('ScreenModel', back_populates='imgs')
    img_url = Column(String)
    metadata_field = Column(JSON, name='metadata')
    created_at = Column(DateTime)

class ScreenService:
    def __init__(self):
        self.__initialize_db()

    def __initialize_db(self):
        with Session(pg_engine) as session:
            session.begin()
            try:
                session.execute(text('''
                    create table if not exists screens (
                        id serial primary key,
                        name text not null,
                        details text,
                        embedding vector(1536) not null,
                        created_at timestamp default current_timestamp
                    )
                '''))

                session.execute(text('''
                    create table if not exists imgs (
                        id serial primary key,
                        screen_id integer references screens(id) on delete cascade,
                        img_url text not null,
                        metadata jsonb,
                        created_at timestamp default current_timestamp
                    );
                '''))
                session.commit()
            except Exception as e:
                session.rollback()
                raise e


    def save(self, screen: ScreenModel):
        with Session(pg_engine) as session:
            session.begin()
            try:
                session.add(screen)
                session.commit()
            except Exception as e:
                session.rollback()
                raise e

    def find_by_similarity(self, query_embedding: List[float]) -> List[ScreenModel]:
        with Session(pg_engine) as session:
            try:
                results = session.scalars(select(ScreenModel).options(joinedload(ScreenModel.imgs)).order_by(ScreenModel.embedding.cosine_distance(query_embedding)).limit(2)).unique().all()

                return [r for r in results]
            except Exception as e:
                logger.error('Exception occurred while querying', e)
            
            return []

            
