import functools

from pymongo import MongoClient
from dataclasses import dataclass, field, fields
import datetime

import time

# MongoDB initialization
client = MongoClient('mongodb://root:example@localhost:27017/')

db = client['smib']

collection = db['state-test']


@dataclass
class BaseDocument:
    _id: any = None

    def __post_init__(self):
        document = collection.find_one()
        if document:
            self.__dict__.update({k:v for k, v in document.items() if k != '_id'})

    def refresh(self):
        self.__post_init__()

    def save(self):
        collection.update_one({}, {'$set': {k:v for k, v in self.__dict__.items() if k != '_id'}}, upsert=True)


class SpaceState(BaseDocument):
    open: bool | None = None
    last_updated: datetime.datetime | None = field(default_factory=lambda: datetime.datetime.now(datetime.timezone.utc))


state = SpaceState()
print(state)

state.open = False
state.last_updated = datetime.datetime.now()
state.save()

print(state)

# document = SpaceState(**collection.find_one() or {})
#
# document.open = True
#
# collection.update_one({}, {'$set': {**document.__dict__}}, upsert=True)
#
# document = SpaceState(**collection.find_one({}) or {})
#
# print(document)