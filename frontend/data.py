from pymongo import MongoClient
import tomli

with open("../system_config.toml", mode="rb") as fp:
    system_config = tomli.load(fp) or None

class Data:
    client = MongoClient('mongodb://127.0.0.1:27017/?directConnection=true&serverSelectionTimeoutMS=2000&appName=mongosh+2.4.2')
    database = client[system_config["api"]["mongodb_db_name"]]
