from flask import Flask, jsonify
import os, socket

app = Flask(__name__)

@app.get("/")
def home():
    return f"""
    <html><head><title>Hello Kubernetes</title></head>
    <body style='font-family:Arial;margin:40px'>
      <h1>Hello from Kubernetes!</h1>
      <p>This page is served by the Python web container.</p>
      <p><b>Pod:</b> {socket.gethostname()}</p>
      <p>Try the API with <code>curl http://localhost:8081/api/hello</code> after port-forwarding it.</p>
    </body></html>
    """

@app.get("/health")
def health():
    return jsonify(status="ok", service="web")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", "8080")))
