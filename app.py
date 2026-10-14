import threading
import time
import uuid
from copy import deepcopy

from flask import Flask, jsonify, render_template, request

app = Flask(__name__)

# ---------------------------------------------------------------------------
# Datos en memoria
# ---------------------------------------------------------------------------
LIBROS_INICIALES = [
    {"id": 1, "titulo": "Cien años de soledad", "autor": "Gabriel García Márquez", "anio": 1967},
    {"id": 2, "titulo": "El amor en los tiempos del cólera", "autor": "Gabriel García Márquez", "anio": 1985},
    {"id": 3, "titulo": "Rayuela", "autor": "Julio Cortázar", "anio": 1963},
]

USUARIOS = {
    "admin": {"password": "admin123", "rol": "administrador"},
    "estudiante": {"password": "clase2026", "rol": "lector"},
}

libros = deepcopy(LIBROS_INICIALES)
siguiente_id = 4
tokens = {}  # token -> nombre de usuario

# Contador de peticiones simultáneas sobre /api/reporte
_candado = threading.Lock()
_activos = 0
LIMITE_SOBRECARGA = 25  # por encima de esto el reporte falla con 500


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------
def usuario_autenticado():
    """Devuelve el nombre de usuario si el header Authorization es válido."""
    cabecera = request.headers.get("Authorization", "")
    if cabecera.startswith("Bearer "):
        return tokens.get(cabecera[len("Bearer "):])
    return None


def requiere_token():
    if usuario_autenticado() is None:
        return jsonify({"error": "Token ausente o inválido"}), 401
    return None


def buscar_libro(libro_id):
    return next((l for l in libros if l["id"] == libro_id), None)


# ---------------------------------------------------------------------------
# Página
# ---------------------------------------------------------------------------
@app.route("/")
def index():
    return render_template("index.html")


# ---------------------------------------------------------------------------
# API
# ---------------------------------------------------------------------------
@app.route("/api/salud", methods=["GET"])
def salud():
    return jsonify({"estado": "ok", "libros": len(libros)})


@app.route("/api/login", methods=["POST"])
def login():
    datos = request.get_json(silent=True) or {}
    nombre = datos.get("usuario")
    clave = datos.get("password")
    usuario = USUARIOS.get(nombre)
    if usuario is None or usuario["password"] != clave:
        return jsonify({"error": "Credenciales inválidas"}), 401

    token = uuid.uuid4().hex
    tokens[token] = nombre
    
    return jsonify({"token": token, "usuario": {"nombre": nombre, **usuario}})


@app.route("/api/libros", methods=["GET"])
def listar_libros():
    texto = request.args.get("q", "").strip().lower()
    resultado = libros
    if texto:
        resultado = [
            l for l in libros
            if texto in l["titulo"].lower() or texto in l["autor"].lower()
        ]
    return jsonify(resultado)


@app.route("/api/libros/<int:libro_id>", methods=["GET"])
def obtener_libro(libro_id):
    libro = buscar_libro(libro_id)
    if libro is None:
        return jsonify({"error": "Libro no encontrado"}), 404
    return jsonify(libro)


@app.route("/api/libros", methods=["POST"])
def crear_libro():
    global siguiente_id
    error = requiere_token()
    if error:
        return error

    datos = request.get_json(silent=True)
    if datos is None:
        return jsonify({"error": "El cuerpo debe ser JSON"}), 400

    # Validación del autor y del año: funciona correctamente.
    autor = (datos.get("autor") or "").strip()
    if not autor:
        return jsonify({"error": "El autor es obligatorio"}), 400
    anio = datos.get("anio")
    if not isinstance(anio, int) or isinstance(anio, bool):
        return jsonify({"error": "El año debe ser un número entero"}), 400

    
    titulo = datos.get("titulo", "")

    libro = {"id": siguiente_id, "titulo": titulo, "autor": autor, "anio": anio}
    siguiente_id += 1
    libros.append(libro)
    return jsonify(libro), 201


@app.route("/api/libros/<int:libro_id>", methods=["PUT"])
def actualizar_libro(libro_id):
    error = requiere_token()
    if error:
        return error

    libro = buscar_libro(libro_id)
    if libro is None:
        return jsonify({"error": "Libro no encontrado"}), 404

    datos = request.get_json(silent=True)
    if datos is None:
        return jsonify({"error": "El cuerpo debe ser JSON"}), 400

    for campo in ("titulo", "autor", "anio"):
        if campo in datos:
            libro[campo] = datos[campo]
    return jsonify(libro)


@app.route("/api/libros/<int:libro_id>", methods=["DELETE"])
def eliminar_libro(libro_id):
    error = requiere_token()
    if error:
        return error

    libro = buscar_libro(libro_id)
    if libro is not None:
        libros.remove(libro)
    
    return jsonify({"mensaje": "Libro eliminado"}), 200


@app.route("/api/reporte", methods=["GET"])
def reporte():
    """
    Endpoint 'pesado'. Simula un recurso compartido que se degrada con la
    concurrencia: cada petición simultánea adicional vuelve más lentas a todas,
    y por encima de LIMITE_SOBRECARGA empieza a fallar.
    """
    global _activos
    with _candado:
        _activos += 1
        concurrentes = _activos
    try:
        
        if concurrentes > LIMITE_SOBRECARGA:
            return jsonify({"error": "Servidor sobrecargado"}), 500
        time.sleep(0.15 + 0.08 * concurrentes)
        return jsonify({
            "total_libros": len(libros),
            "autores_distintos": len({l["autor"] for l in libros}),
            "concurrentes_en_este_momento": concurrentes,
        })
    finally:
        with _candado:
            _activos -= 1


@app.route("/api/reset", methods=["POST"])
def reiniciar():
    """Restaura los datos iniciales. Útil entre una práctica y otra."""
    global libros, siguiente_id
    libros = deepcopy(LIBROS_INICIALES)
    siguiente_id = 4
    tokens.clear()
    return jsonify({"mensaje": "Datos restaurados"})


if __name__ == "__main__":
    # threaded=True es necesario para que JMeter genere concurrencia real.
    app.run(host="127.0.0.1", port=5000, debug=False, threaded=True)
