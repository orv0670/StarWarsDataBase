"""
This module takes care of starting the API Server, Loading the DB and Adding the endpoints
"""
import os
from flask import Flask, request, jsonify, url_for, json
from flask_migrate import Migrate
from flask_swagger import swagger
from flask_cors import CORS
from utils import APIException, generate_sitemap
from admin import setup_admin
from models import db, User, Personajes, Planetas, Favoritos
import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
#from models import Person

app = Flask(__name__)
app.url_map.strict_slashes = False
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DB_CONNECTION_STRING')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
MIGRATE = Migrate(app, db)
db.init_app(app)
CORS(app)
setup_admin(app)
jwt = JWTManager(app)

# Handle/serialize errors like a JSON object
@app.errorhandler(APIException)
def handle_invalid_usage(error):
    return jsonify(error.to_dict()), error.status_code

# generate sitemap with all your endpoints
@app.route('/')
def sitemap():
    return generate_sitemap(app)
#bloque de GET's
@app.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    list_users = list(map(lambda users: users.serialize(), users))
    return jsonify(list_users), 200

@app.route('/users/<int:user_id>',methods=['GET'])
def get_user(user_id):
    user = User.query.get(user_id)
    if user is None:
        raise APIException('este usuario no existe en la base de datos', status_code=404)
    userjson = user.serialize()
    return jsonify(userjson), 200

@app.route('/personajes', methods=['GET'])
def get_personajes():
    personajes = Personajes.query.all()
    list_personajes = list(map(lambda personajes: personajes.serialize(), personajes))
    return jsonify(list_personajes)

@app.route('/planetas', methods=['GET'])
def get_planetas():
    planetas = Planetas.query.all()
    list_planetas = list(map(lambda planetas: planetas.serialize(), planetas))
    return jsonify(list_planetas)

@app.route('/personajes/<int:personaje_id>', methods=['GET'])
def get_personaje(personaje_id):
    personaje = Personajes.query.get(personaje_id)
    if personaje is None:
        raise APIException('El personaje no existe', status_code=404)
    personajejson = personaje.serialize()
    return jsonify(personajejson),200

@app.route('/planetas/<int:planeta_id>', methods=['GET'])
def get_planeta(planeta_id):
    planeta = Planetas.query.get(planeta_id)
    if planeta is None:
        raise APIException('El planeta no existe', status_code=404)
    planetajson = planeta.serialize()
    return jsonify(planetajson)

@app.route('/favoritos/', methods=['GET'])
def get_favoritos_usuario():
    all_favoritos = Favoritos.query.all()
    lista_favoritos = list(map(lambda favoritos: favoritos.serialize(), all_favoritos))
    #favoritos_usuario = list(filter(lambda user_fav: user_fav['user_id'] == user_id, lista_favoritos))
    return jsonify(lista_favoritos)

@app.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    if request.method == 'GET':
        token = get_jwt_identity()
        return jsonify({"success": "Acceso a espacio privado", "usuario": token}), 200

# bloque de metodos POST
@app.route('/favoritos', methods=['POST'])
@jwt_required()
def agregar_favorito():
    request_body = request.get_json()
    favorito = Favoritos(nombre_favorito = request_body["nombre_favorito"], type_favorito = request_body["type_favorito"], user_id = request_body["user_id"])
    db.session.add(favorito)
    db.session.commit()
    return jsonify({"msg": "el favorito se ha agregado con exito"})

@app.route('/personajes', methods=['POST'])
def agregar_personaje():
    request_body = request.get_json()
    personaje = Personajes(name = request_body["name"], height = request_body["height"], mass = request_body["mass"], hair_color = request_body["hair_color"], skin_color = request_body["skin_color"], eye_color = request_body["eye_color"], birth_year = request_body["birth_year"], gender = request_body["gender"])
    db.session.add(personaje)
    db.session.commit()
    return jsonify({"msg": "el personaje se agrego con exito"})

@app.route('/planetas', methods=['POST'])
def agregar_planeta():
    request_body = request.get_json()
    planeta = Planetas(name = request_body["name"], population = request_body["population"], terrain = request_body["terrain"], diameter = request_body["diameter"], rotation_period = request_body["rotation_period"], orbital_period = request_body["orbital_period"], gravity = request_body["gravity"], climate = request_body["climate"], surface_water = request_body["surface_water"])
    db.session.add(planeta)
    db.session.commit()
    return jsonify({"msg": "el planeta se agrego con exito!"}),200

@app.route('/register', methods=["POST"])
def register():
    if request.method == 'POST':
        email = request.json.get("email", None)
        password = request.json.get("password", None)

        if not email:
            return jsonify({"msg": "el email es requerido, por favor ingreselo"}), 400
        if not password:
            return jsonify({"msg": "la contraseña es requerida, por favor ingresela"}), 400

        user = User.query.filter_by(email=email).first()
        if user:
            return jsonify({"msg": "el usuario ya existe"}), 400

        user = User()
        user.email = email
        hashed_password = generate_password_hash(password)
        print(password, hashed_password)

        user.password = hashed_password

        db.session.add(user)
        db.session.commit()

        return jsonify({"exito!": "gracias, su regristro fue exitoso", "status": "true"}), 200


@app.route('/login', methods=['POST'])
def login():
    if request.method == 'POST':
        email = request.json.get("email", None)
        password = request.json.get("password", None)

        if not email:
            return jsonify({"msg": "el email es requerido, por favor ingreselo"}), 400
        if not password:
            return jsonify({"msg": "la contraseña es requerida, por favor ingresela"}), 400

        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify({"msg": "Usuario o contraseña incorrecta"}), 401

        if not check_password_hash(user.password, password):
            return jsonify({"msg": "Usuario o contraseña incorrecta"}), 401

        # crear el token
        expiracion = datetime.timedelta(days=1)
        access_token = create_access_token(identity=user.email, expires_delta=expiracion)

        data = {
            "user": user.serialize(),
            "token": access_token,
            "expires": expiracion.total_seconds()*1000
        }

        return jsonify(data), 200

#bloque de DELETE(favoritos)
@app.route('/favoritos/<int:favorito_id>', methods=['DELETE'])
def borrar_favorito(favorito_id):
    favorito = Favoritos.query.get(favorito_id)
    if favorito is None:
        raise APIException('favorito no encontrado', status_code=404)
    db.session.delete(favorito)
    db.session.commit()
    return jsonify({"msg": "el favorito se elimino con exito"}),200


# this only runs if `$ python src/main.py` is executed
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 3000))
    app.run(host='0.0.0.0', port=PORT, debug=False)
