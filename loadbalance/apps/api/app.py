from flask import Flask, jsonify, request
import os, socket

app = Flask(__name__)

@app.get("/")
def root():
    return jsonify(service="api", message="Python API is running", pod=socket.gethostname())

@app.get("/api/hello")
def hello():
    name = request.args.get("name", "World")
    return jsonify(message=f"Hello, {name}!", pod=socket.gethostname())

@app.post("/api/hello")
def hello_post():
    body = request.get_json(silent=True) or {}
    name = body.get("name", "World")
    return jsonify(message=f"Hello, {name}!", pod=socket.gethostname())

@app.get("/health")
def health():
    return jsonify(status="ok", service="api")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
