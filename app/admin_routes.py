from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app
from flask_login import login_required, current_user
from app import db
from app.models import User, Product, Category, Brand, Country, News, Setting, SeoMeta
from app.forms.product_forms import ProductForm
from app.utilities.helpers import transliterate, generate_slug, save_product_image, save_brand_image, \
    save_category_image, save_news_image
from app.utilities.template_utils import get_site_setting, get_seo_meta
import os
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


# === Дашборд админки ===
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
                main_path, thumbnail_path = save_product_image(
                    form.image.data,
                    form.name.data,
                    0,  # Временный ID
                    current_app
                )
                product.image_url = main_path
            except Exception as e:
                flash(f'Ошибка при загрузке изображения: {str(e)}', 'error')
                return render_template('admin/product_form.html',
                                       form=form,
                                       title='Создать товар',
                                       categories=all_categories)

        db.session.add(product)
        db.session.flush()  # Чтобы получить ID

        # Обновляем slug с учетом ID
        product.slug = f"{product.id}-{transliterate(product.name)}"

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
                main_path, thumbnail_path = save_product_image(
                    form.image.data,
                    form.name.data,
                    product.id,
                    current_app
                )
                product.image_url = main_path
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
    custom_slug = request.form.get('slug', '').strip()

    if name:
        # Генерируем slug
        if custom_slug:
            slug = transliterate(custom_slug)
        else:
            slug = transliterate(name)

        # Проверяем уникальность slug
        existing_slugs = [cat.slug for cat in Category.query.all()]
        slug = generate_slug(slug, existing_slugs)

        category = Category(name=name, slug=slug)
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


@admin.route('/admin/categories/edit/<int:category_id>', methods=['GET', 'POST'])
@admin_required
def edit_category(category_id):
    category = Category.query.get_or_404(category_id)

    if request.method == 'POST':
        name = request.form.get('name')
        custom_slug = request.form.get('slug', '').strip()

        if name:
            category.name = name

            # Генерируем slug
            if custom_slug:
                slug = transliterate(custom_slug)
            else:
                slug = transliterate(name)

            # Проверяем уникальность slug (исключая текущую категорию)
            existing_slugs = [cat.slug for cat in Category.query.filter(Category.id != category_id).all()]
            slug = generate_slug(slug, existing_slugs)
            category.slug = slug

            db.session.commit()
            flash('Категория успешно обновлена', 'success')
            return redirect(url_for('admin.categories'))
        else:
            flash('Название категории не может быть пустым', 'error')

    return render_template('admin/category_form.html', category=category)


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

            # Обработка изображения
            if 'image' in request.files:
                image_file = request.files['image']
                if image_file and image_file.filename:
                    try:
                        image_url = save_news_image(image_file, title, 0, current_app)  # 0 - временный ID
                        news.image_url = image_url
                    except Exception as e:
                        flash(f'Ошибка при загрузке изображения: {str(e)}', 'error')
                        return render_template('admin/news_form.html', title='Создать новость')

            db.session.add(news)
            db.session.flush()  # Чтобы получить ID

            # Обновляем slug с учетом ID
            news.slug = f"{news.id}-{transliterate(news.title)}"

            # Обновляем изображение с правильным ID
            if 'image' in request.files and request.files['image'].filename:
                try:
                    image_file = request.files['image']
                    image_url = save_news_image(image_file, news.title, news.id, current_app)
                    news.image_url = image_url
                except Exception as e:
                    flash(f'Ошибка при обновлении изображения: {str(e)}', 'warning')

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

            # Обработка изображения
            if 'image' in request.files:
                image_file = request.files['image']
                if image_file and image_file.filename:
                    try:
                        image_url = save_news_image(image_file, title, news.id, current_app)
                        news.image_url = image_url
                    except Exception as e:
                        flash(f'Ошибка при загрузке изображения: {str(e)}', 'error')
                        return render_template('admin/news_form.html', news=news, title='Редактировать новость')

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


# === Управление настройками сайта ===
@admin.route('/admin/settings')
@admin_required
def settings():
    """Страница настроек сайта"""
    settings = Setting.query.order_by(Setting.key).all()
    return render_template('admin/settings.html', settings=settings)


@admin.route('/admin/settings/edit/<int:setting_id>', methods=['GET', 'POST'])
@admin_required
def edit_setting(setting_id):
    """Редактирование настройки"""
    setting = Setting.query.get_or_404(setting_id)

    if request.method == 'POST':
        value = request.form.get('value')
        description = request.form.get('description')

        if value is not None:
            setting.value = value
            if description:
                setting.description = description
            db.session.commit()
            flash('Настройка успешно обновлена', 'success')
            return redirect(url_for('admin.settings'))
        else:
            flash('Значение не может быть пустым', 'error')

    return render_template('admin/setting_form.html', setting=setting)


# === Управление SEO настройками ===
@admin.route('/admin/seo')
@admin_required
def seo_settings():
    """Страница SEO настроек"""
    seo_settings = SeoMeta.query.order_by(SeoMeta.page_type, SeoMeta.page_id).all()
    return render_template('admin/seo_settings.html', seo_settings=seo_settings)


@admin.route('/admin/seo/edit/<int:seo_id>', methods=['GET', 'POST'])
@admin_required
def edit_seo_setting(seo_id):
    """Редактирование SEO настройки"""
    seo = SeoMeta.query.get_or_404(seo_id)

    if request.method == 'POST':
        title = request.form.get('title')
        description = request.form.get('description')
        keywords = request.form.get('keywords')
        robots = request.form.get('robots')
        og_title = request.form.get('og_title')
        og_description = request.form.get('og_description')
        og_image = request.form.get('og_image')

        seo.title = title
        seo.description = description
        seo.keywords = keywords
        seo.robots = robots
        seo.og_title = og_title
        seo.og_description = og_description
        seo.og_image = og_image

        db.session.commit()
        flash('SEO настройка успешно обновлена', 'success')
        return redirect(url_for('admin.seo_settings'))

    return render_template('admin/seo_form.html', seo=seo)


@admin.route('/admin/seo/create', methods=['GET', 'POST'])
@admin_required
def create_seo_setting():
    """Создание новой SEO настройки"""
    if request.method == 'POST':
        page_type = request.form.get('page_type')
        page_id = request.form.get('page_id')
        title = request.form.get('title')
        description = request.form.get('description')
        keywords = request.form.get('keywords')
        robots = request.form.get('robots')
        og_title = request.form.get('og_title')
        og_description = request.form.get('og_description')
        og_image = request.form.get('og_image')

        if page_type:
            try:
                page_id = int(page_id) if page_id else None
            except (ValueError, TypeError):
                page_id = None

            seo = SeoMeta(
                page_type=page_type,
                page_id=page_id,
                title=title,
                description=description,
                keywords=keywords,
                robots=robots,
                og_title=og_title,
                og_description=og_description,
                og_image=og_image
            )
            db.session.add(seo)
            db.session.commit()
            flash('SEO настройка успешно создана', 'success')
            return redirect(url_for('admin.seo_settings'))
        else:
            flash('Тип страницы обязателен', 'error')

    # Получаем список доступных страниц для выбора
    products = Product.query.limit(10).all()
    categories = Category.query.all()
    news_items = News.query.limit(10).all()

    return render_template('admin/seo_form.html',
                           title='Создать SEO настройку',
                           products=products,
                           categories=categories,
                           news_items=news_items)


@admin.route('/admin/seo/delete/<int:seo_id>')
@admin_required
def delete_seo_setting(seo_id):
    """Удаление SEO настройки"""
    seo = SeoMeta.query.get_or_404(seo_id)
    db.session.delete(seo)
    db.session.commit()
    flash('SEO настройка успешно удалена', 'success')
    return redirect(url_for('admin.seo_settings'))


# === Управление Sitemap ===
@admin.route('/admin/sitemap/generate')
@admin_required
def generate_sitemap():
    """Генерация статического sitemap.xml"""
    try:
        # Импортируем функции для генерации
        from flask import current_app
        from app.sitemap_routes import sitemap_xml

        # Генерируем sitemap
        with current_app.test_request_context('/sitemap.xml'):
            response = sitemap_xml()

            # Сохраняем в статический файл
            static_folder = os.path.join(current_app.root_path, 'static')
            sitemap_path = os.path.join(static_folder, 'sitemap.xml')

            # Создаем папку если её нет
            os.makedirs(static_folder, exist_ok=True)

            # Записываем содержимое в файл
            with open(sitemap_path, 'w', encoding='utf-8') as f:
                f.write(response.get_data(as_text=True))

            flash('Sitemap успешно сгенерирован и сохранен', 'success')
    except Exception as e:
        flash(f'Ошибка при генерации sitemap: {str(e)}', 'error')

    return redirect(url_for('admin.dashboard'))


@admin.route('/admin/sitemap/view')
@admin_required
def view_sitemap():
    """Просмотр sitemap"""
    try:
        from flask import current_app
        static_folder = os.path.join(current_app.root_path, 'static')
        sitemap_path = os.path.join(static_folder, 'sitemap.xml')

        if os.path.exists(sitemap_path):
            with open(sitemap_path, 'r', encoding='utf-8') as f:
                sitemap_content = f.read()
            return render_template('admin/sitemap_view.html', sitemap_content=sitemap_content)
        else:
            flash('Sitemap файл не найден. Сгенерируйте его сначала.', 'warning')
            return redirect(url_for('admin.generate_sitemap'))
    except Exception as e:
        flash(f'Ошибка при чтении sitemap: {str(e)}', 'error')
        return redirect(url_for('admin.dashboard'))