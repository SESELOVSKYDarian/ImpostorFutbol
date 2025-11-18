from flask import Flask, jsonify, send_from_directory
import os

from hola import get_random_player

app = Flask(__name__)

# Ruta donde está tu HTML
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "impostor_game.html")

@app.route("/api/get-footballer")
def get_footballer():
    """
    Obtiene un jugador aleatorio usando la lógica compartida de hola.py.
    """
    try:
        data = get_random_player()

        # Enviar al HTML solo el jugador conocido
        return jsonify({
            "id": data.get("id"),
            "name": data.get("name"),
            "age": data.get("age"),
            "nationality": data.get("nationality"),
            "position": data.get("position"),
            "team": data.get("team_id"),  # ← usar team_id porque eso devuelve hola.py
            "team_name": data.get("team_name"),
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500



# ¡IMPORTANTE! Permite servir archivos estáticos del mismo directorio
@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(BASE_DIR, path)


if __name__ == "__main__":
    app.run(debug=True)
