import asyncio
import datetime
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from pymongo import MongoClient

from pydantic_mongo_document import Document

uri = "mongodb://root:example@localhost:27017/"

client = MongoClient(uri)
ping_result = client.admin.command("ping")

Document.set_mongo_uri(uri)
Document.__database__ = "smib_plugins"
Document.__collection__ = "space_state_2"


class SpaceState(Document):
    open: bool = None
    last_updated: datetime.datetime = None


async def main():
    state = SpaceState()
    state.open = True

    await state.insert()

    print(state)

if __name__ == "__main__":
    asyncio.run(main())
