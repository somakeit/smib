from pydantic import BaseModel
from pymongo import MongoClient
from pymongodantic import Model, MongoModel

client = MongoClient("mongodb://localhost:27017/")
db = client["database_name"]


class SpaceState(BaseModel, MongoModel):
    open: bool
    motion: bool


# Insert data
new_state = SpaceState(open=False, motion=True)
new_state.save(db.space_state)

# Fetch data
db_state = SpaceState.fetch(db.space_state, new_state.id)
print(db_state)
