from flask import Flask
from flask_cors import CORS

from routes.games import games_bp
from routes.players import players_bp
from routes.predict import predict_bp
from routes.explain import explain_bp
from routes.chatbot import chatbot_bp
from flask import request



app = Flask(__name__)
CORS(app)

app.register_blueprint(games_bp, url_prefix="/api")
app.register_blueprint(players_bp, url_prefix="/api")
app.register_blueprint(predict_bp, url_prefix="/api")
app.register_blueprint(explain_bp, url_prefix="/api")
app.register_blueprint(chatbot_bp, url_prefix="/api")


@app.get("/api/health")
def health():
    return {"status": "ok"}

@app.post("/")
def debug_root_post():
    print("=== Unexpected POST / ===")
    print("Remote address:", request.remote_addr)
    print("User-Agent:", request.headers.get("User-Agent"))
    print("Origin:", request.headers.get("Origin"))
    print("Referer:", request.headers.get("Referer"))
    print("Body:", request.get_data(as_text=True))
    return {"error": "Unexpected POST to root"}, 404

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
