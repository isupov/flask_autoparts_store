from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from app import db

# Промежуточная таблица для связи many-to-many Product-Category
product_category = db.Table('product_category',
                            db.Column('product_id', db.Integer, db.ForeignKey('product.id'), primary_key=True),
                            db.Column('category_id', db.Integer, db.ForeignKey('category.id'), primary_key=True)
                            )


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Связь с корзиной
    cart_items = db.relationship('CartItem', backref='user', lazy=True)

    def set_password(self, password):
        """Установка пароля"""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Проверка пароля"""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.username}>'


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False)  # Для URL
    parent_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Связь с подкатегориями
    children = db.relationship('Category', backref=db.backref('parent', remote_side=[id]))

    # Связь с товарами
    products = db.relationship('Product', secondary=product_category, back_populates='categories')

    def __repr__(self):
        return f'<Category {self.name}>'

    def is_parent(self):
        return self.parent_id is None

    def get_full_name(self):
        """Возвращает полное имя категории с учетом родителей"""
        if self.parent:
            return f"{self.parent.name} → {self.name}"
        return self.name

    def get_full_slug(self):
        """Возвращает полный slug с учетом родителей"""
        if self.parent:
            return f"{self.parent.slug}/{self.slug}"
        return self.slug

    def get_total_products_count(self):
        """Возвращает общее количество товаров в категории и подкатегориях"""
        count = len(self.products)
        for child in self.children:
            count += len(child.products)
        return count


class Brand(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    slug = db.Column(db.String(100), unique=True, nullable=False)  # Для URL
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Связь с товарами
    products = db.relationship('Product', backref='brand', lazy=True)

    def __repr__(self):
        return f'<Brand {self.name}>'


class Country(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False, unique=True)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    # Связь с товарами
    products = db.relationship('Product', backref='country', lazy=True)

    def __repr__(self):
        return f'<Country {self.name}>'


class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)  # Для URL
    article = db.Column(db.String(50), unique=True, nullable=False)
    short_desc = db.Column(db.Text)
    full_desc = db.Column(db.Text)
    image_url = db.Column(db.String(200))  # Основное изображение
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False, default=0)  # Количество на складе
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    brand_id = db.Column(db.Integer, db.ForeignKey('brand.id'), nullable=False)
    country_id = db.Column(db.Integer, db.ForeignKey('country.id'), nullable=False)

    # Связи
    categories = db.relationship('Category', secondary=product_category, back_populates='products')
    cart_items = db.relationship('CartItem', backref='product', lazy=True)

    def get_thumbnail_url(self):
        """Генерирует URL миниатюры из URL основного изображения"""
        if self.image_url:
            # Заменяем расширение файла на _thumb.расширение
            path_parts = self.image_url.split('/')
            if len(path_parts) > 0:
                filename = path_parts[-1]  # Получаем имя файла
                name_parts = filename.split('.')
                if len(name_parts) > 1:
                    # Добавляем _thumb перед расширением
                    name_parts[-2] = name_parts[-2] + '_thumb'
                    thumbnail_filename = '.'.join(name_parts)
                    # Заменяем имя файла на имя миниатюры
                    path_parts[-1] = thumbnail_filename
                    return '/'.join(path_parts)
        return self.image_url  # Возвращаем оригинальное изображение если миниатюра не найдена

    def __repr__(self):
        return f'<Product {self.name}>'


class CartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f'<CartItem {self.user_id}:{self.product_id}>'


class News(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False)  # Для URL
    content = db.Column(db.Text, nullable=False)
    image_url = db.Column(db.String(200))  # Изображение новости
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    def __repr__(self):
        return f'<News {self.title}>'

    def get_thumbnail_url(self):
        """Генерирует URL миниатюры из URL основного изображения"""
        if self.image_url:
            # Разбиваем путь на части
            path_parts = self.image_url.split('/')
            if len(path_parts) > 0:
                filename = path_parts[-1]  # Получаем имя файла
                name_parts = filename.split('.')
                if len(name_parts) > 1:
                    # Добавляем _thumb перед расширением
                    name_parts[-2] = name_parts[-2] + '_thumb'
                    thumbnail_filename = '.'.join(name_parts)
                    # Заменяем имя файла на имя миниатюры
                    path_parts[-1] = thumbnail_filename
                    return '/'.join(path_parts)
        return self.image_url  # Возвращаем оригинальное изображение если миниатюра не найдена


class Setting(db.Model):
    """Модель для хранения настроек сайта"""
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)  # Ключ настройки
    value = db.Column(db.Text)  # Значение настройки
    description = db.Column(db.String(200))  # Описание настройки
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    def __repr__(self):
        return f'<Setting {self.key}>'

    @staticmethod
    def get(key, default=None):
        """Получение значения настройки по ключу"""
        setting = Setting.query.filter_by(key=key).first()
        return setting.value if setting else default

    @staticmethod
    def set(key, value, description=None):
        """Установка значения настройки"""
        setting = Setting.query.filter_by(key=key).first()
        if setting:
            setting.value = str(value)
            if description:
                setting.description = description
        else:
            setting = Setting(key=key, value=str(value), description=description)
            db.session.add(setting)
        db.session.commit()
        return setting


class SeoMeta(db.Model):
    """Модель для хранения SEO мета-тегов"""
    id = db.Column(db.Integer, primary_key=True)
    page_type = db.Column(db.String(50), nullable=False)  # Тип страницы (main, catalog, product, etc.)
    page_id = db.Column(db.Integer)  # ID конкретной страницы (для product, category и т.д.)
    title = db.Column(db.String(200))  # Title страницы
    description = db.Column(db.Text)  # Meta description
    keywords = db.Column(db.Text)  # Meta keywords
    robots = db.Column(db.String(100), default='index, follow')  # Robots meta tag
    og_title = db.Column(db.String(200))  # Open Graph title
    og_description = db.Column(db.Text)  # Open Graph description
    og_image = db.Column(db.String(200))  # Open Graph image
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    def __repr__(self):
        return f'<SeoMeta {self.page_type}:{self.page_id}>'

    @staticmethod
    def get_for_page(page_type, page_id=None):
        """Получение SEO настроек для конкретной страницы"""
        if page_id:
            # Сначала ищем специфичные настройки для страницы
            seo = SeoMeta.query.filter_by(page_type=page_type, page_id=page_id).first()
            if seo:
                return seo
        # Если нет специфичных, ищем общие настройки для типа страницы
        return SeoMeta.query.filter_by(page_type=page_type, page_id=None).first()