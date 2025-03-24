from pymongo import MongoClient
from utilities import SystemConfig
system_config = SystemConfig.system_config

class Data:
    client = MongoClient('mongodb://127.0.0.1:27017/?directConnection=true&serverSelectionTimeoutMS=2000&appName=mongosh+2.4.2')
    database = client[system_config["api"]["mongodb_db_name"]]
