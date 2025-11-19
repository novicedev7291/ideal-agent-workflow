from typing import List

from app.core.pg import pg_engine
from app.core.config import config

from services.screen_service import ScreenModel

from sqlalchemy.orm import Session
from sqlalchemy import text, select
from pgvector.sqlalchemy.vector import Vector
from openai import OpenAI

import numpy
from sklearn.preprocessing import normalize

client = OpenAI(
    api_key=config.OPEN_AI_KEY
)

from app.core.logging import get_logger

logger = get_logger(__name__)

def __normalize(vector: List[float]) -> List[float]:
    vector_np = numpy.array(vector, dtype=numpy.float32)

    normalized = normalize(vector_np.reshape(1, -1), 'l2')

    return normalized[0].tolist()


def similarity_check(user_query: str):
    resp = client.embeddings.create(
        model='text-embedding-3-small',
        input=user_query
    )

    query_embedding = __normalize(resp.data.pop().embedding)

    with Session(pg_engine) as session:
        try:
            computed_col = (ScreenModel.embedding.cosine_distance(query_embedding)).label('similarity')
            query = select(
                ScreenModel.name,
                computed_col
            ).order_by(
                ScreenModel.embedding.cosine_distance(query_embedding)
            ).limit(5)

            results = session.execute(query)

            for r in results:
                print(r.name, r.similarity)
        except Exception as e:
            logger.exception('Error occurred while querying the DB : ', e)