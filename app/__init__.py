from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config import Config
import os

# Создаем экземпляры расширений глобально
db = SQLAlchemy()
login_manager = LoginManager()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # Создаем папки для загрузок если их нет
    for folder_type, folder_path in app.config['UPLOAD_FOLDERS'].items():
        os.makedirs(folder_path, exist_ok=True)

    # Инициализируем расширения с приложением
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Пожалуйста, войдите для доступа к этой странице.'

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))

    # Добавляем функции в контекст Jinja2
    from app.utilities.template_utils import template_functions
    @app.context_processor
    def inject_utilities():
        return template_functions

    # Регистрация blueprint'ов
    from app.routes import main
    from app.auth_routes import auth
    from app.admin_routes import admin
    from app.cart_routes import cart
    from app.profile_routes import profile
    from app.sitemap_routes import sitemap
    from app.robots_routes import robots

    app.register_blueprint(main)
    app.register_blueprint(auth)
    app.register_blueprint(admin)
    app.register_blueprint(cart)
    app.register_blueprint(profile)
    app.register_blueprint(sitemap)
    app.register_blueprint(robots)

    return app