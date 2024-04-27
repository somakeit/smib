import functools

from pymongo import MongoClient
from dataclasses import dataclass, field, fields
import datetime

# MongoDB initialization
client = MongoClient('mongodb://root:example@localhost:27017/')
db = client['smib']


def database(collection_name):
    collection = db[collection_name]

    def decorator(cls):
        cls = dataclass(cls)

        class Wrapper:
            def __init__(self, *args, **kwargs):
                document = collection.find_one() or {}

                default_instance = cls(*args, **kwargs)

                for f in fields(cls):
                    value = document.get(f.name, getattr(default_instance, f.name))
                    setattr(self, f.name, value)

                self.wrapped = default_instance

                def save(self):
                    # get a dictionary of all instance variables excluding 'wrapped'
                    obj_dict = {k: v for k, v in self.__dict__.items() if k != 'wrapped'}
                    collection.update_one({}, {'$set': obj_dict}, upsert=True)

            def __getattr__(self, name):
                # Get the latest document from the database
                document = collection.find_one() or {}
                self.__dict__ = document
                # if document has updated value of name, return it. Otherwise return the value from dataclass instance
                return document.get(name, getattr(self.wrapped, name))

            def __setattr__(self, field, value):
                if field != 'wrapped':
                    collection.update_one({}, {'$set': {field: value, "_updated_at": datetime.datetime.now()}}, upsert=True)
                super().__setattr__(field, value)

            def reset(self):
                obj = cls.__new__(cls)  # Create new instance without calling __init__
                cls.__init__(obj)  # Call __init__ to initialize the new instance
                collection.update_one({}, {'$set': obj.__dict__}, upsert=True)


    # Copying class name and docstring
            __repr__ = cls.__repr__
            __name__ = cls.__name__
            __doc__ = cls.__doc__
            __qualname__ = cls.__qualname__

        return Wrapper

    return decorator


@database('SpaceStateCollection')
class SpaceState:
    open: bool = False
    motion: bool = True
    _updated_at: datetime.datetime = field(default_factory=datetime.datetime.now)


state = SpaceState()
state.open = True

print(state.open)

state.open = False
state.motion = False

print(state)


print(state)
