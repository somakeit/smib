from bson import ObjectId
from pymongo import MongoClient
from dataclasses import dataclass, field
from datetime import datetime, timezone

# MongoDB initialization
client = MongoClient('mongodb://root:example@localhost:27017/')
db = client['<your_database>']
collection = db['<your_collection>']


@dataclass
class SpaceState:
    _id: ObjectId = None
    open: bool = None
    last_updated: datetime | None = field(default_factory=lambda: datetime.now(timezone.utc))


class SpaceStateRepository:

    @staticmethod
    def get() -> SpaceState:
        """Retrieve a single SpaceState document by its unique id"""
        document = collection.find_one({})
        if not document:
            _ = collection.insert_one({})
            document = collection.find_one({})
        return SpaceState(**document)

    @staticmethod
    def update(space_state: SpaceState):
        """Update a SpaceState document by giving only the fields to update"""
        document = vars(space_state)
        document.pop('_id', None)
        document["last_updated"] = datetime.now()
        result = collection.update_one({}, {"$set": document}, upsert=True)
        if not result.matched_count:
            raise Exception("Failed to update SpaceState.")


initial_state = SpaceStateRepository.get()
print(initial_state)  # Initial state

# Update the state
updated_state = SpaceState(open=True)
SpaceStateRepository.update(updated_state)

final_state = SpaceStateRepository.get()
print(final_state)  # Updated state
