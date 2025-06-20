import logging
from functools import cache
from logging import Logger
from typing import TypeVar, Any, Callable

from beanie import init_beanie, Document
from motor.motor_asyncio import AsyncIOMotorClient

from smib.config import MONGO_DB_URL, MONGO_DB_NAME
from smib.utilities.package import get_actual_module_name, get_module_from_name

T = TypeVar('T', bound=Any)


def get_all_subclasses(cls: type[T]) -> set[type[T]]:
    subclasses = set(cls.__subclasses__())
    for subclass in subclasses.copy():
        subclasses.update(get_all_subclasses(subclass))
    return subclasses

def filter_not_beanie(model: type[Document]) -> bool:
    return not model.__module__.startswith('beanie')


class DatabaseManager:
    def __init__(self, db_name: str = MONGO_DB_NAME) -> None:
        self.db_name: str = db_name
        self.client: AsyncIOMotorClient[Any] = AsyncIOMotorClient(MONGO_DB_URL)
        self.logger: Logger = logging.getLogger(self.__class__.__name__)
        self._document_filters: list[Callable[[type[Document]], bool]] = []

        self.register_document_filter(filter_not_beanie)

    @cache
    def get_all_document_models(self) -> list[type[Document]]:
        all_documents = get_all_subclasses(Document)
        filtered_documents = all_documents
        for filter_func in self._document_filters:
            filtered_documents = set(filter(filter_func, filtered_documents))
        return list(filtered_documents)

    def register_document_filter(self, filter: Callable[[type[Document]], bool]) -> None:
        self._document_filters.append(filter)

    async def initialise(self) -> None:
        all_documents = self.get_all_document_models()
        self.logger.info(f"Initializing database '{self.db_name}' with {len(all_documents)} document(s)")
        if all_documents:
            self.logger.info(f"Documents: {', '.join(doc.__name__ for doc in all_documents)}")
        await init_beanie(database=self.client[self.db_name], document_models=all_documents)

    def find_model_by_name(self, model_name: str, plugin_name: str | None = None) -> type[Document] | None:
        def plugin_filter(module: str) -> str | None:
            if not plugin_name:
                return None
            return get_actual_module_name(get_module_from_name(module.split('.')[0]))

        return next(
            (
                model
                for model in self.get_all_document_models()
                if model.__name__ == model_name
                   and (plugin_filter(model.__module__) == plugin_name if plugin_name else True)
            ),
            None,
        )

    async def get_db_version(self) -> str:
        info = await self.client.server_info()
        return info['version']
