import os


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///car_shop.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Структурированные папки для разных типов контента
    UPLOAD_FOLDERS = {
        'products': os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'static', 'uploads', 'products'),
        'brands': os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'static', 'uploads', 'brands'),
        'categories': os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'static', 'uploads',
                                   'categories'),
        'news': os.path.join(os.path.dirname(os.path.abspath(__file__)), 'app', 'static', 'uploads', 'news')
    }

    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

    # Логирование
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT')