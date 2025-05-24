from flask import Flask
from app.frontend.routes import main_bp
app = Flask(__name__, template_folder="app/frontend/templates")

app.register_blueprint(main_bp)

if __name__ == "__main__":
    app.run(debug=True)

