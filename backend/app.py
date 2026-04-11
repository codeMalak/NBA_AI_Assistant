from flask import Flask
from flask_cors import CORS

from routes.predict import predict_bp
from routes.explain import explain_bp

app = Flask(__name__)
CORS(app)

app.register_blueprint(predict_bp, url_prefix="/api")
app.register_blueprint(explain_bp, url_prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)