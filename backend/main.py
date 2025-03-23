from pymongo import MongoClient

# Connect to MongoDB
client = MongoClient('mongodb://127.0.0.1:27017/')

# Access the database
db = client['tmp_discord']

# Access the collection
collection = db['collection']

# Insert a document
document = {"name": "John", "age": 30, "city": "New York"}
collection.insert_one(document)

# Query the document
result = collection.find_one({"name": "John"})
print(result)

# Update the document
collection.update_one({"name": "John"}, {"$set": {"age": 31}})

# Delete the document
collection.delete_one({"name": "John"})
