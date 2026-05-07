from flask import Flask
from config import Config
from flask_login import LoginManager
from models import db
from models import User

app = Flask(__name__)
app.config.from_object(Config)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

db.init_app(app)
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    return "ToDo App"

if __name__ == "__main__":
    app.run(debug=True)