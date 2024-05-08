from pymongo import MongoClient
from datetime import datetime
from dataclasses import dataclass, field, asdict
from abc import ABCMeta, ABC

mongo_client = MongoClient("mongodb://root:example@localhost:27017/")
db = mongo_client["your_database"]
collection = db["your_collection"]


def init_collection_with_sample_doc():
    collection.insert_one({"open": False, "last_updated": datetime.now().isoformat()})


init_collection_with_sample_doc()


class CacheMeta(ABCMeta):
    def __new__(cls, name, bases, dct):
        new_class = super().__new__(cls, name, bases, dct)
        new_class._cache = {}
        new_class._sync = True
        return new_class

    def __enter__(cls):
        doc = cls.collection.find_one()
        for key in doc.keys():
            setattr(cls, key, doc[key])
        cls._sync = False
        return cls

    def __exit__(cls, *_args):
        cls._sync = True
        cls.collection.update_one({}, {"$set": cls._cache}, upsert=True)

    def __setattr__(cls, key, value):
        if key == "_sync":
            super().__setattr__(key, value)
        elif cls._sync:
            cls.collection.update_one({}, {"$set": {key: value}})
            cls._cache[key] = value
        else:
            cls._cache[key] = value

    def __getattribute__(cls, item):
        if item in cls._cache and cls._sync:
            doc = cls.collection.find_one()
            return doc.get(item)
        else:
            return super().__getattribute__(item)


@dataclass
class SpaceState(metaclass=CacheMeta):
    collection = collection
    open: bool = False
    last_updated: str = field(default=None)


print(SpaceState.open)

with SpaceState:
    SpaceState.open = True

print(SpaceState.open)
