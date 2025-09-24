from flask import Flask, request, jsonify
import hashlib


app = Flask(__name__)


def compute_token(uid: str) -> str:
    return hashlib.sha1(uid.encode()).hexdigest()


@app.route("/create_file", methods=["POST"])
def http_create_file():
    try:
        auth = request.headers.get("Authorization", "")
        if not auth.startswith("Bearer "):
            return jsonify({"status": "ERROR", "message": "token requerido"}), 401

        token = auth.split(" ", 1)[1]

        body = request.get_json(silent=True) or {}
        uid = body.get("uid")
        filename = body.get("filename")
        content = body.get("content", "")

        if not uid or not filename:
            return jsonify({"status": "ERROR", "message": "uid y filename requeridos"}), 400

        # Validar token = sha1(UID)
        if token != compute_token(uid):
            return jsonify({"status": "ERROR", "message": "token inválido"}), 403

        # Guardar fichero en disco en el cwd
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)

        return jsonify({"status": "OK", "filename": filename}), 200
    except Exception as exc:
        return jsonify({"status": "ERROR", "message": str(exc)}), 500


if __name__ == "__main__":
    # Arranca el microservicio de ficheros en 0.0.0.0:5051
    app.run(host="127.0.0.1", port=5051, debug=True)


