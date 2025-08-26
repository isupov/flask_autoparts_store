from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models import User, Product, Category, Brand, Country, News
from app.forms.product_forms import ProductForm
import os
from werkzeug.utils import secure_filename
from PIL import Image
import uuid

admin = Blueprint('admin', __name__)


def admin_required(func):
    """Декоратор для проверки прав администратора"""
    from functools import wraps

    @wraps(func)
    def decorated_view(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if not current_user.is_admin:
            flash('Доступ запрещен. Недостаточно прав.', 'error')
            return redirect(url_for('main.index'))
        return func(*args, **kwargs)

    return decorated_view


def save_picture(form_picture):
    """Сохранение и оптимизация изображения с созданием миниатюр"""
    random_hex = uuid.uuid4().hex
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads', picture_fn)

    # Создаем папку если её нет
    os.makedirs(os.path.dirname(picture_path), exist_ok=True)

    # Оптимизируем основное изображение (800x800)
    output_size = (800, 800)
    img = Image.open(form_picture)
    img.thumbnail(output_size)
    img.save(picture_path)

    # Создаем миниатюру (300x300)
    thumbnail_fn = random_hex + '_thumb' + f_ext
    thumbnail_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads', thumbnail_fn)

    # Создаем квадратную миниатюру 300x300
    thumbnail_size = (300, 300)
    img_thumb = Image.open(form_picture)

    # Преобразуем в RGB если нужно (для PNG с прозрачностью)
    if img_thumb.mode in ('RGBA', 'LA', 'P'):
        img_thumb = img_thumb.convert('RGB')

    # Создаем квадратную миниатюру с обрезкой по центру
    img_thumb.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)

    # Если изображение не квадратное, обрезаем до квадрата
    if img_thumb.size[0] != img_thumb.size[1]:
        # Находим меньшую сторону
        min_side = min(img_thumb.size)
        # Обрезаем до квадрата по центру
        left = (img_thumb.size[0] - min_side) // 2
        top = (img_thumb.size[1] - min_side) // 2
        right = left + min_side
        bottom = top + min_side
        img_thumb = img_thumb.crop((left, top, right, bottom))

    img_thumb = img_thumb.resize(thumbnail_size, Image.Resampling.LANCZOS)
    img_thumb.save(thumbnail_path)

    return picture_fn  # Возвращаем только имя основного файла


@admin.route('/admin')
@admin_required
def dashboard():
    # Статистика для админки
    stats = {
        'users_count': User.query.count(),
        'products_count': Product.query.count(),
        'categories_count': Category.query.count(),
        'news_count': News.query.count()
    }
    return render_template('admin/dashboard.html', stats=stats)


# === Управление пользователями ===
@admin.route('/admin/users')
@admin_required
def users():
    page = request.args.get('page', 1, type=int)
    users = User.query.paginate(page=page, per_page=10)
    return render_template('admin/users.html', users=users)


@admin.route('/admin/users/toggle_admin/<int:user_id>')
@admin_required
def toggle_admin(user_id):
    user = User.query.get_or_404(user_id)
    if user.id == current_user.id:
        flash('Нельзя изменить свои права администратора', 'error')
    else:
        user.is_admin = not user.is_admin
        db.session.commit()
        flash(f'Права пользователя {user.username} успешно изменены', 'success')
    return redirect(url_for('admin.users'))


# === Управление товарами ===
@admin.route('/admin/products')
@admin_required
def products():
    page = request.args.get('page', 1, type=int)
    products = Product.query.paginate(page=page, per_page=10)
    return render_template('admin/products.html', products=products)


@admin.route('/admin/products/create', methods=['GET', 'POST'])
@admin_required
def create_product():
    form = ProductForm()
    # Заполняем выпадающие списки
    form.brand_id.choices = [(b.id, b.name) for b in Brand.query.all()]
    form.country_id.choices = [(c.id, c.name) for c in Country.query.all()]

    # Получаем все категории с полными именами
    all_categories = Category.query.all()
    form.category_ids.choices = [(c.id, c.get_full_name()) for c in all_categories]

    if form.validate_on_submit():
        product = Product(
            name=form.name.data,
            article=form.article.data,
            short_desc=form.short_desc.data,
            full_desc=form.full_desc.data,
            price=form.price.data,
            stock=form.stock.data,
            brand_id=form.brand_id.data,
            country_id=form.country_id.data
        )

        # Обработка изображения
        if form.image.data:
            try:
                picture_file = save_picture(form.image.data)
                product.image_url = f'/static/uploads/{picture_file}'
            except Exception as e:
                flash(f'Ошибка при загрузке изображения: {str(e)}', 'error')
                return render_template('admin/product_form.html',
                                       form=form,
                                       title='Создать товар',
                                       categories=all_categories)

        db.session.add(product)
        db.session.commit()

        # Добавляем категории
        category_ids = request.form.getlist('category_ids')
        for cat_id in category_ids:
            try:
                category = Category.query.get(int(cat_id))
                if category:
                    product.categories.append(category)
            except (ValueError, TypeError):
                continue

        db.session.commit()
        flash('Товар успешно создан', 'success')
        return redirect(url_for('admin.products'))

    return render_template('admin/product_form.html',
                           form=form,
                           title='Создать товар',
                           categories=all_categories)


@admin.route('/admin/products/edit/<int:product_id>', methods=['GET', 'POST'])
@admin_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    form = ProductForm(obj=product)

    # Заполняем выпадающие списки
    form.brand_id.choices = [(b.id, b.name) for b in Brand.query.all()]
    form.country_id.choices = [(c.id, c.name) for c in Country.query.all()]

    # Получаем все категории с полными именами
    all_categories = Category.query.all()
    form.category_ids.choices = [(c.id, c.get_full_name()) for c in all_categories]

    if form.validate_on_submit():
        # Обновляем поля товара
        product.name = form.name.data
        product.article = form.article.data
        product.short_desc = form.short_desc.data
        product.full_desc = form.full_desc.data
        product.price = form.price.data
        product.stock = form.stock.data
        product.brand_id = form.brand_id.data
        product.country_id = form.country_id.data

        # Обработка изображения
        if form.image.data:
            try:
                picture_file = save_picture(form.image.data)
                product.image_url = f'/static/uploads/{picture_file}'
            except Exception as e:
                flash(f'Ошибка при загрузке изображения: {str(e)}', 'error')
                return render_template('admin/product_form.html',
                                       form=form,
                                       product=product,
                                       title='Редактировать товар',
                                       categories=all_categories)

        # Обновляем категории
        product.categories.clear()
        category_ids = request.form.getlist('category_ids')
        for cat_id in category_ids:
            try:
                category = Category.query.get(int(cat_id))
                if category:
                    product.categories.append(category)
            except (ValueError, TypeError):
                continue

        db.session.commit()
        flash('Товар успешно обновлен', 'success')
        return redirect(url_for('admin.products'))

    # Предзаполняем форму текущими значениями
    form.category_ids.data = [c.id for c in product.categories] if product.categories else []

    return render_template('admin/product_form.html',
                           form=form,
                           product=product,
                           title='Редактировать товар',
                           categories=all_categories)

@admin.route('/admin/products/delete/<int:product_id>')
@admin_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Товар успешно удален', 'success')
    return redirect(url_for('admin.products'))


# === Управление категориями ===
@admin.route('/admin/categories')
@admin_required
def categories():
    # Получаем только родительские категории
    parent_categories = Category.query.filter_by(parent_id=None).all()
    # Получаем все категории для выпадающего списка
    all_categories = Category.query.all()
    return render_template('admin/categories.html',
                           parent_categories=parent_categories,
                           all_categories=all_categories)


@admin.route('/admin/categories/create', methods=['POST'])
@admin_required
def create_category():
    name = request.form.get('name')
    parent_id = request.form.get('parent_id')

    if name:
        category = Category(name=name)
        if parent_id and parent_id != '0':
            try:
                category.parent_id = int(parent_id)
            except (ValueError, TypeError):
                pass

        db.session.add(category)
        db.session.commit()
        flash('Категория успешно создана', 'success')
    else:
        flash('Название категории не может быть пустым', 'error')
    return redirect(url_for('admin.categories'))


@admin.route('/admin/categories/delete/<int:category_id>')
@admin_required
def delete_category(category_id):
    category = Category.query.get_or_404(category_id)
    if category.products:
        flash('Нельзя удалить категорию, содержащую товары', 'error')
    else:
        db.session.delete(category)
        db.session.commit()
        flash('Категория успешно удалена', 'success')
    return redirect(url_for('admin.categories'))


# === Управление брендами ===
@admin.route('/admin/brands')
@admin_required
def brands():
    brands = Brand.query.all()
    return render_template('admin/brands.html', brands=brands)


@admin.route('/admin/brands/create', methods=['POST'])
@admin_required
def create_brand():
    name = request.form.get('name')
    if name:
        brand = Brand(name=name)
        db.session.add(brand)
        db.session.commit()
        flash('Бренд успешно создан', 'success')
    else:
        flash('Название бренда не может быть пустым', 'error')
    return redirect(url_for('admin.brands'))


@admin.route('/admin/brands/delete/<int:brand_id>')
@admin_required
def delete_brand(brand_id):
    brand = Brand.query.get_or_404(brand_id)
    if brand.products:
        flash('Нельзя удалить бренд, содержащий товары', 'error')
    else:
        db.session.delete(brand)
        db.session.commit()
        flash('Бренд успешно удален', 'success')
    return redirect(url_for('admin.brands'))


# === Управление странами ===
@admin.route('/admin/countries')
@admin_required
def countries():
    countries = Country.query.all()
    return render_template('admin/countries.html', countries=countries)


@admin.route('/admin/countries/create', methods=['POST'])
@admin_required
def create_country():
    name = request.form.get('name')
    if name:
        country = Country(name=name)
        db.session.add(country)
        db.session.commit()
        flash('Страна успешно создана', 'success')
    else:
        flash('Название страны не может быть пустым', 'error')
    return redirect(url_for('admin.countries'))


@admin.route('/admin/countries/delete/<int:country_id>')
@admin_required
def delete_country(country_id):
    country = Country.query.get_or_404(country_id)
    if country.products:
        flash('Нельзя удалить страну, содержащую товары', 'error')
    else:
        db.session.delete(country)
        db.session.commit()
        flash('Страна успешно удалена', 'success')
    return redirect(url_for('admin.countries'))


# === Управление новостями ===
@admin.route('/admin/news')
@admin_required
def news():
    page = request.args.get('page', 1, type=int)
    news_items = News.query.order_by(News.created_at.desc()).paginate(page=page, per_page=10)
    return render_template('admin/news.html', news=news_items)


@admin.route('/admin/news/create', methods=['GET', 'POST'])
@admin_required
def create_news():
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        if title and content:
            news = News(title=title, content=content)
            db.session.add(news)
            db.session.commit()
            flash('Новость успешно создана', 'success')
            return redirect(url_for('admin.news'))
        else:
            flash('Заголовок и содержание новости обязательны', 'error')

    return render_template('admin/news_form.html', title='Создать новость')


@admin.route('/admin/news/edit/<int:news_id>', methods=['GET', 'POST'])
@admin_required
def edit_news(news_id):
    news = News.query.get_or_404(news_id)
    if request.method == 'POST':
        title = request.form.get('title')
        content = request.form.get('content')
        if title and content:
            news.title = title
            news.content = content
            db.session.commit()
            flash('Новость успешно обновлена', 'success')
            return redirect(url_for('admin.news'))
        else:
            flash('Заголовок и содержание новости обязательны', 'error')

    return render_template('admin/news_form.html', news=news, title='Редактировать новость')


@admin.route('/admin/news/delete/<int:news_id>')
@admin_required
def delete_news(news_id):
    news = News.query.get_or_404(news_id)
    db.session.delete(news)
    db.session.commit()
    flash('Новость успешно удалена', 'success')
    return redirect(url_for('admin.news'))