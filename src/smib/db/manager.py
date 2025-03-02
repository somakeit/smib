import logging
from logging import Logger

from beanie import init_beanie, Document
from motor.motor_asyncio import AsyncIOMotorClient
from smib.config import MONGO_DB_URL, MONGO_DB_NAME


class DatabaseManager:
    def __init__(self, db_name: str = MONGO_DB_NAME):

        self.db_name: str = db_name
        self.client: AsyncIOMotorClient = AsyncIOMotorClient(MONGO_DB_URL)
        self.logger: Logger = logging.getLogger(self.__class__.__name__)

    @staticmethod
    def get_all_document_models():
        all_documents = get_all_subclasses(Document)
        filtered_documents = filter(lambda doc: not doc.__module__.startswith('beanie'), all_documents)

        return list(filtered_documents)

    async def initialise(self):
        all_documents = self.get_all_document_models()
        self.logger.info(f"Initialising database {self.db_name} with {len(all_documents)} document(s)")
        self.logger.info(f"Documents: {", ".join([doc.__name__ for doc in all_documents])}")
        await init_beanie(database=self.client[self.db_name], document_models=all_documents)

def get_all_subclasses(cls):
    """Recursively get all subclasses of a given class."""
    subclasses = set(cls.__subclasses__())
    for subclass in cls.__subclasses__():
        subclasses.update(get_all_subclasses(subclass))
    return subclasses
