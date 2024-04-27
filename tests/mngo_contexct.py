from enum import StrEnum, auto
from typing import Type, TypeVar

from pymongo import MongoClient
from pymongo.client_session import ClientSession
from datetime import datetime, timezone
from dataclasses import dataclass, field, fields, asdict

from pymongo.collection import Collection

# mongo_client = MongoClient("mongodb://root:example@localhost:27017/")
# db = mongo_client["your_database"]
# collection = db["your_collection"]

global_cache = {}
_sync = True


class SingletonMongoDB:

    collection: Collection
    client: MongoClient
    session: ClientSession

    @classmethod
    def set_collection(cls, name):
        mongo_client = MongoClient("mongodb://root:example@localhost:27017/")
        db = mongo_client['smib_plugins']
        cls.collection = db[name]
        cls.client = mongo_client
        return cls

    def __post_init__(self):
        global global_cache
        global_cache = asdict(self)
        document = self.collection.find_one()
        if document is None:
            _ = self.collection.update_one({}, {"$set": asdict(self)}, upsert=True)
            document = self.collection.find_one()

        global_cache.update({k: v for k, v in document.items() if k in global_cache})

    def __setattr__(self, key, value):
        global global_cache, _sync
        if key in global_cache and _sync:
            self.collection.update_one({}, {"$set": {key: value}})
        elif not _sync:
            global_cache[key] = value

        super().__setattr__(key, value)

    def __getattribute__(self, item):
        # Check for methods
        if callable(method := super().__getattribute__(item)):
            return method

        global global_cache, _sync
        if item in global_cache and _sync:
            doc = self.collection.find_one()
            if doc:
                return doc.get(item)
        elif not _sync:
            return global_cache.get(item, None)

        return super().__getattribute__(item)

    def __enter__(self):
        global _sync, global_cache

        self.session = self.client.start_session()
        self.session.start_transaction()

        # On entering the context, update the local cache with contents from db
        doc = self.collection.find_one()
        for field_name in global_cache.keys():
            if field_name in doc:
                global_cache[field_name] = doc[field_name]
        _sync = False
        return self

    def __exit__(self, *args):
        global _sync, global_cache
        _sync = True
        # On exiting the context, update the db with contents from the local cache
        self.collection.update_one({}, {"$set": global_cache}, upsert=True)
        self.session.commit_transaction()


Database = SingletonMongoDB.set_collection('space_openclose')


class Trigger(StrEnum):
    TOGGLE = auto()
    BUTTON = auto()


@dataclass
class SpaceState(Database):
    open: bool = False
    last_updated: datetime = datetime.now(tz=timezone.utc)
    motion: bool = False
    open_closed_last_trigger: str = None

    def toggle_open(self):
        self.open = not self.open
        self.open_closed_last_trigger = Trigger.TOGGLE.value

    def set_space_open(self):
        self.open = True
        self.open_closed_last_trigger = Trigger.BUTTON.value

    def set_space_closed(self):
        self.open = False
        self.open_closed_last_trigger = Trigger.BUTTON.value

    def __setattr__(self, name, value):
        super().__setattr__(name, value)
        if name != "last_updated":
            self.last_updated = datetime.now(tz=timezone.utc)


if __name__ == '__main__':
    with SpaceState() as space:
        print(space)
        space.toggle_open()
        print(space)

    space = SpaceState()
    space.set_space_open()
    print(space)
    space.set_space_closed()
    print(space)
