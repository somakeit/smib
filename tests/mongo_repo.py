from bson import ObjectId
from pymongo import MongoClient
from datetime import datetime, timezone
from dataclasses import dataclass, field, fields
from typing import TypeVar, Type, Optional

# MongoDB initialization
client = MongoClient('mongodb://root:example@localhost:27017/')
db = client['<your_database>']
collection = db['<your_collection>']

T = TypeVar('T')


class RepositoryMeta(type):

    _id: ObjectId = None

    def get(cls: Type[T]) -> T:
        document = collection.find_one({})
        if not document:
            _ = collection.insert_one({})
            document = collection.find_one({})
        document.pop('_id', None)
        return cls(**document)

    def update(cls: Type[T], item: T) -> T | None:
        document = vars(item)
        document.pop('_id', None)  # Exclude the '_id' field
        document["last_updated"] = datetime.now(timezone.utc)
        updated_document = collection.find_one_and_update({}, {"$set": document}, return_document=True)
        if updated_document is None:
            return None
        updated_document.pop('_id', None)
        result = cls(**updated_document)
        return result


@dataclass
class SpaceState(metaclass=RepositoryMeta):
    open: bool = None
    last_updated: datetime | None = field(default_factory=lambda: datetime.now(timezone.utc))
    _sync: bool = field(default=False, init=False, repr=False)
    _collection = collection

    def __enter__(self):
        self._sync = True
        return self

    def __exit__(self, *args):
        self._sync = False

    def __getattribute__(self, name):
        sync = super().__getattribute__('_sync')
        # Check if the name is a field in the dataclass
        if sync and any(f.name == name for f in fields(self)):
            document = self._collection.find_one({})
            return document.get(name) if document else None
        return super().__getattribute__(name)

    def __setattr__(self, name, value):
        sync = super().__getattribute__('_sync')
        if sync and name in fields(self):
            self._collection.find_one_and_update({}, {"$set": {name: value}})
        super().__setattr__(name, value)

    def __getitem__(self, name):
        return self.__getattribute__(name)

    def __setitem__(self, name, value):
        return self.__setattr__(name, value)


# Usage:
with SpaceState() as state:
    print(state.open)  # This will fetch from database
    state.open = False  # This will update in database

print(SpaceState())
