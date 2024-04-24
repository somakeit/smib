from pymongo import MongoClient

# Step 1: Connect to MongoDB
# Default connection url for local MongoDB instance.
client = MongoClient('mongodb://localhost:27017/')

# Step 2: Create database
db = client['smib']

# Step 3: Create collection
collection = db['users']

# Step 4: Insert a document into the collection
new_user = {"name": "John Doe", "email": "john@example.com", "space_open": True}
insert_result = collection.insert_one(new_user)
print(f"Added user with id: {insert_result.inserted_id}")

# Step 5: Retrieve all documents from the collection
for user in collection.find():
    print(user)

from pymongo import MongoClient

class MongoDBWrapper:
    def __init__(self, db_name, collection_name):
        self.client = MongoClient("mongodb://localhost:27017/")
        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

    def __getattr__(self, field_name):
        def method(value=None):
            if value is None:
                return self.collection.find({field_name: {"$exists": True}})
            else:
                return self.collection.find({field_name: value})

        return method


# Usage:
wrapper = MongoDBWrapper("smib", "users")
for doc in wrapper.space_open():
    print(next(wrapper.space_open()))
