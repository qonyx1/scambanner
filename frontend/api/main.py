# from fastapi import FastAPI
# import uvicorn

# app = FastAPI()

# @app.get("/")
# def read_root():
#     return {"message": "Welcome to the FastAPI backend!"}


# if __name__ == "__main__":
#     uvicorn.run(app, host="127.0.0.1", port=8000)



import pymongo

client = pymongo.MongoClient("mongodb://localhost:27017/")

