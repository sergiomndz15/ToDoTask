from flask import Flask, request, jsonify
from datetime import datetime
from bson import ObjectId
from config import get_db

app = Flask(__name__)
db = get_db()

# Helper para formatear ObjectId
def format_object_id(id):
    return str(id)

# Ruta para iniciar sesión
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({"error": "Falta nombre de usuario o contraseña"}), 400

    # Buscar al usuario en la base de datos
    user = db.users.find_one({"username": username})

    if not user:
        return jsonify({"error": "Usuario no encontrado"}), 404

    if user['password'] != password:
        return jsonify({"error": "Contraseña incorrecta"}), 401

    # Si el usuario y la contraseña son correctos, devolver el user_id
    return jsonify({"message": "Inicio de sesión exitoso", "user_id": str(user['_id'])}), 200


# Ruta para registrar un nuevo usuario
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    if not data.get('username') or not data.get('password'):
        return jsonify({"error": "Falta nombre de usuario o contraseña"}), 400

    user = {
        "username": data['username'],
        "password": data['password']
    }
    db.users.insert_one(user)
    return jsonify({"message": "Usuario registrado con éxito"}), 201

@app.route('/tasks/<user_id>', methods=['GET'])
def get_tasks(user_id):
    tasks = db.tasks.find({"user_id": user_id})
    task_list = []
    for task in tasks:
        task['_id'] = str(task['_id'])
        task_list.append(task)
    return jsonify(task_list), 200  # Devuelve una lista directamente

# Ruta para cambiar el estado de una tarea
@app.route('/task/<task_id>', methods=['PATCH'])
def update_task_status(task_id):
    data = request.json
    new_status = data.get('status')

    if new_status not in ["To-Do", "En proceso", "Finalizado"]:
        return jsonify({"error": "Estado inválido"}), 400

    task = db.tasks.find_one({"_id": ObjectId(task_id)})

    if not task:
        return jsonify({"error": "Tarea no encontrada"}), 404

    update_data = {"status": new_status}
    if new_status == "En proceso" and not task.get("start_time"):
        update_data["start_time"] = datetime.utcnow()
    elif new_status == "Finalizado":
        update_data["end_time"] = datetime.utcnow()

    db.tasks.update_one({"_id": ObjectId(task_id)}, {"$set": update_data})
    return jsonify({"message": "Estado de tarea actualizado"}), 200

# Ruta para obtener las tareas de un usuario
@app.route('/tasks/<user_id>', methods=['GET'])
def get_tasks(user_id):
    tasks = db.tasks.find({"user_id": user_id})
    task_list = []
    for task in tasks:
        task['_id'] = format_object_id(task['_id'])
        task_list.append(task)
    return jsonify(task_list), 200

if __name__ == '__main__':
    app.run(debug=True)
