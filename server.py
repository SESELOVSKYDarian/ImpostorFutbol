from flask import Flask, jsonify, send_from_directory
import subprocess
import json
import os

app = Flask(__name__)

# Ruta donde está tu HTML
BASE_DIR = os.path.dirname(os.path.abspath(__file__))


@app.route("/")
def index():
    return send_from_directory(BASE_DIR, "impostor_game.html")

@app.route("/api/get-footballer")
def get_footballer():
    """
    Corre hola.py, obtiene el JSON y devuelve solo el jugador elegido.
    """
    try:
        result = subprocess.check_output(
            ["python", "hola.py"], 
            stderr=subprocess.STDOUT,
            text=True
        )

        data = json.loads(result)

        if not data or "id" not in data:
            return jsonify({"error": "El script no devolvió datos válidos."}), 500

        # Enviar al HTML solo el jugador conocido
        return jsonify({
            "id": data.get("id"),
            "name": data.get("name"),
            "age": data.get("age"),
            "nationality": data.get("nationality"),
            "position": data.get("position"),
            "team": data.get("team_id")   # ← usar team_id porque eso devuelve hola.py
        })

    except subprocess.CalledProcessError as e:
        return jsonify({
            "error": "Error ejecutando hola.py",
            "details": e.output
        }), 500

    except Exception as e:
        return jsonify({"error": str(e)}), 500



# ¡IMPORTANTE! Permite servir archivos estáticos del mismo directorio
@app.route("/<path:path>")
def static_files(path):
    return send_from_directory(BASE_DIR, path)


if __name__ == "__main__":
    app.run(debug=True)
