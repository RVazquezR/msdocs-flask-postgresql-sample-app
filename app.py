import os
from datetime import datetime
from flask import Flask, jsonify, render_template, request, send_from_directory
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect

app = Flask(__name__, static_folder='static')
csrf = CSRFProtect(app)

# Configuración según entorno
if 'WEBSITE_HOSTNAME' not in os.environ:
    print("Loading config.development and environment variables from .env file.")
    app.config.from_object('azureproject.development')
else:
    print("Loading config.production.")
    app.config.from_object('azureproject.production')

app.config.update(
    SQLALCHEMY_DATABASE_URI=app.config.get('DATABASE_URI'),
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
)

# === Inicialización base de datos ===
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# === MODELO ===
class ImagenProcesada(db.Model):
    __tablename__ = 'imagen_procesada'
    id = db.Column(db.Integer, primary_key=True)
    usuario = db.Column(db.String(50))
    nombre_archivo = db.Column(db.String(100))
    rojo = db.Column(db.Integer)
    verde = db.Column(db.Integer)
    azul = db.Column(db.Integer)
    fecha_hora = db.Column(db.DateTime)

# === RUTAS ===

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/registro', methods=['POST'])
@csrf.exempt
def registro():
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No se recibió JSON'}), 400

    try:
        imagen = ImagenProcesada(
            usuario=data.get('usuario'),
            nombre_archivo=data.get('nombreArchivo'),
            rojo=int(data.get('rojo')),
            verde=int(data.get('verde')),
            azul=int(data.get('azul')),
            fecha_hora=datetime.fromisoformat(data.get('fechaHora'))
        )
        db.session.add(imagen)
        db.session.commit()
        return jsonify({'mensaje': 'Registro guardado'}), 201
    except Exception as e:
        return jsonify({'error': f'Error procesando datos: {str(e)}'}), 500

@app.route('/subir_con_imagen', methods=['POST'])
@csrf.exempt
def subir_con_imagen():
    try:
        usuario = request.form.get('usuario')
        nombre_archivo = request.form.get('nombreArchivo')
        rojo = int(request.form.get('rojo'))
        verde = int(request.form.get('verde'))
        azul = int(request.form.get('azul'))
        fecha_hora = datetime.fromisoformat(request.form.get('fechaHora'))

        imagen = ImagenProcesada(
            usuario=usuario,
            nombre_archivo=nombre_archivo,
            rojo=rojo,
            verde=verde,
            azul=azul,
            fecha_hora=fecha_hora
        )
        db.session.add(imagen)
        db.session.commit()

        upload_dir = os.path.join(app.static_folder, 'images')
        os.makedirs(upload_dir, exist_ok=True)

        for key in ['original', 'byn', 'pixelada']:
            if key in request.files:
                f = request.files[key]
                save_path = os.path.join(upload_dir, f"{imagen.id}_{key}.bmp")
                f.save(save_path)

        return jsonify({'mensaje': 'Datos e imágenes subidos correctamente'}), 201
    except Exception as e:
        return jsonify({'error': f'Error: {str(e)}'}), 500

@app.route('/datos', methods=['GET'])
def datos():
    registros = ImagenProcesada.query.order_by(ImagenProcesada.fecha_hora.desc()).all()

    def imagen_existe(id, tipo):
        path = os.path.join(app.static_folder, 'images', f"{id}_{tipo}.bmp")
        return os.path.exists(path)

    return jsonify([
        {
            'id': r.id,
            'usuario': r.usuario,
            'nombreArchivo': r.nombre_archivo,
            'rojo': r.rojo,
            'verde': r.verde,
            'azul': r.azul,
            'fechaHora': r.fecha_hora.isoformat(),
            'hasOriginal': imagen_existe(r.id, 'original'),
            'hasByn': imagen_existe(r.id, 'byn'),
            'hasPixelada': imagen_existe(r.id, 'pixelada')
        } for r in registros
    ])

@app.route('/imagenes/<int:id>/<tipo>.bmp')
def imagen(id, tipo):
    filename = f"{id}_{tipo}.bmp"
    path = os.path.join(app.static_folder, 'images', filename)
    if os.path.exists(path):
        return send_from_directory(os.path.join(app.static_folder, 'images'), filename)
    return "Imagen no encontrada", 404

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == '__main__':
    app.run()

