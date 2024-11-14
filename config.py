from pymongo import MongoClient

def get_db():
    client = MongoClient("mongodb+srv://23300058:<db_password>@myapi.umx1u.mongodb.net/todo_app?retryWrites=true&w=majority")
    db = client['todo_app']
    return db
