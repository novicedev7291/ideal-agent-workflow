import os
import numpy

from dataclasses import dataclass
from typing import List

from openai import OpenAI

from sklearn.preprocessing import normalize

from app.core.logging import get_logger
from app.core.config import config
from services.screen_service import ImageModel, ScreenModel, ScreenService

logger = get_logger(__name__)

@dataclass
class ImageInfo:
    url: str

@dataclass
class Screen:
    id: int
    name: str
    content: str
    imgs: List[ImageInfo]

class KnowledgeBase:
    def __init__(self, screen_svc: ScreenService):
        self.service = screen_svc
        self.openai = OpenAI(api_key=config.OPEN_AI_KEY)


    def __normalize(self, vector: List[float]) -> List[float]:
        vector_np = numpy.array(vector, dtype=numpy.float32)

        normalized = normalize(vector_np.reshape(1, -1), 'l2')

        return normalized[0].tolist()

    def ingest_screen(self, title:str, chunk: str, imgs: List[str]):
        try:
            resp = self.openai.embeddings.create(
                model='text-embedding-3-small',
                input=chunk
            )

            logger.debug(f'OpenAI embedding response success? : {resp.data is not None}')

            if resp.data:
                logger.debug(f'No of embeddings in openai resp : {len(resp.data)}')

                embeddings = resp.data.pop().embedding

                n_embeddings = self.__normalize(embeddings)

                screen = ScreenModel(
                    name=title,
                    details=chunk,
                    imgs=[ImageModel(img_url=img) for img in imgs],
                    embedding=n_embeddings
                )

                self.service.save(screen)
                
        except Exception as e:
            logger.error(f'Error occurred while ingesting', e)
            

    def search_screens(self, query: str) -> List[Screen]:
        try:
            resp = self.openai.embeddings.create(
                model='text-embedding-3-small',
                input=query
            )

            logger.debug(f'OpenAI embedding response success? : {resp.data is not None}')

            if resp.data:
                logger.debug(f'Embedding result from OpenAI length : {len(resp.data)}')

                query_embedding = self.__normalize(resp.data.pop().embedding)

                db_results = self.service.find_by_similarity(query_embedding)

                #TODO: tweak distance if results are not satisfactory
                filtered_results = [r for r in db_results if r.distance < 0.50]

                filtered_results.sort(key=lambda x: x.distance)

                results = []
                for r in filtered_results:
                    results.append(Screen(
                        id=r.id,
                        name=r.name,
                        content=r.details,
                        imgs=[ImageInfo(url=url) for url in r.imgs],
                    ))

                logger.debug(f'Results from DB : {len(results)}')
                return results
        except Exception as e:
            logger.error('Exception occurred while searching', e)
        
        return []