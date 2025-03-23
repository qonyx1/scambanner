from pymongo import MongoClient

class Data:
    client = MongoClient('mongodb://127.0.0.1:27017/')
    database = client['tmp_discord']
