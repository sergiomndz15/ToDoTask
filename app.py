from flask import Flask, request, jsonify, session
from datetime import datetime
from bson import ObjectId
from config import get_db

app = Flask(__name__)
app.secret_key = "tu_clave_secreta"  # Asegúrate de tener una clave secreta para sesiones
db = get_db()

# Helper para formatear ObjectId
def format_object_id(id):
    return str(id)

# Ruta para registrar un nuevo usuario
@app.route('/register', methods=['POST'])
def register():
    data = request.json
    if not data.get('username') or not data.get('password'):
        return jsonify({"error": "Falta nombre de usuario o contraseña"}), 400

    # Verifica si el usuario ya existe
    existing_user = db.users.find_one({"username": data['username']})
    if existing_user:
        return jsonify({"error": "El nombre de usuario ya está en uso"}), 400

    user = {
        "username": data['username'],
        "password": data['password']
    }
    db.users.insert_one(user)
    return jsonify({"message": "Usuario registrado con éxito"}), 201

# Ruta para hacer login de un usuario
@app.route('/login', methods=['POST'])
def login():
    data = request.json
    if not data.get('username') or not data.get('password'):
        return jsonify({"error": "Falta nombre de usuario o contraseña"}), 400

    user = db.users.find_one({"username": data['username']})
    if user and user['password'] == data['password']:
        session['user_id'] = data['username']  # Usamos el nombre de usuario como ID
        return jsonify({"message": "Login exitoso", "user_id": data['username']}), 200
    return jsonify({"error": "Usuario o contraseña incorrectos"}), 400

# Ruta para agregar una tarea
@app.route('/task', methods=['POST'])
def create_task():
    data = request.json  # Obtener los datos JSON enviados desde el frontend
    
    user_id = data.get('user_id')  # Obtener el ID del usuario
    title = data.get('title')  # Obtener el título de la tarea
    
    if not user_id or not title:
        return jsonify({"error": "Falta ID de usuario o título de la tarea"}), 400
    
    task = {
        "user_id": user_id,
        "title": title,
        "status": "To-Do",  # Estado por defecto
        "start_time": None,
        "end_time": None
    }
    
    # Insertar la tarea en la base de datos
    result = db.tasks.insert_one(task)
    
    if result.inserted_id:
        return jsonify({"message": "Tarea creada con éxito", "task_id": str(result.inserted_id)}), 201
    else:
        return jsonify({"error": "Error al crear la tarea"}), 500
# Ruta para obtener las tareas de un usuario
@app.route('/tasks/<user_id>', methods=['GET'])
def get_tasks(user_id):
    tasks = db.tasks.find({"user_id": user_id})  # Obtener las tareas del usuario por ID
    task_list = []
    
    for task in tasks:
        task['_id'] = str(task['_id'])  # Convertir ObjectId a string para mostrarlo correctamente
        task_list.append(task)

    return jsonify(task_list), 200  # Devolver todas las tareas del usuario

@app.route('/task/<task_id>', methods=['PATCH'])
def update_task_status(task_id):
    data = request.json
    user_id = data.get('user_id')  # Obtener el user_id del JSON

    if not user_id:
        return jsonify({"error": "Usuario no autenticado"}), 401

    new_status = data.get('status')
    if new_status not in ["To-Do", "En proceso", "Finalizado"]:
        return jsonify({"error": "Estado inválido"}), 400

    task = db.tasks.find_one({"_id": ObjectId(task_id), "user_id": user_id})  # Buscar por user_id también

    if not task:
        return jsonify({"error": "Tarea no encontrada"}), 404

    update_data = {"status": new_status}
    if new_status == "En proceso" and not task.get("start_time"):
        update_data["start_time"] = datetime.utcnow()
    elif new_status == "Finalizado":
        update_data["end_time"] = datetime.utcnow()
        # Eliminar tarea cuando está finalizada
        db.tasks.delete_one({"_id": ObjectId(task_id)})

    db.tasks.update_one({"_id": ObjectId(task_id)}, {"$set": update_data})
    
    # Depurar datos actualizados
    updated_task = db.tasks.find_one({"_id": ObjectId(task_id)})
    print(f"Updated task: {updated_task}")
    
    return jsonify({"message": "Estado de tarea actualizado"}), 200

if __name__ == '__main__':
    app.run(debug=True)
