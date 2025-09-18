from flask import Blueprint, render_template, request, jsonify, url_for, abort, flash, redirect
from flask_login import current_user, login_required
from app import db
from app.models import Product, News, Category, Brand, Country, product_category, CartItem
from sqlalchemy import or_, func
from app.utils import transliterate
import re

main = Blueprint('main', __name__)


# Функции для нормализации текста поиска
def normalize_text_for_search(text):
    """Нормализует текст для поиска - убирает лишние пробелы и приводит к нижнему регистру"""
    if not text:
        return ""
    return re.sub(r'\s+', ' ', str(text).strip().lower())


def advanced_search_in_text(text, search_query):
    """Продвинутый поиск в тексте - регистронезависимо, с нормализацией"""
    if not text or not search_query:
        return False

    normalized_text = normalize_text_for_search(text)
    normalized_query = normalize_text_for_search(search_query)

    # Проверяем точное совпадение
    if normalized_query in normalized_text:
        return True

    # Проверяем частичные совпадения слов
    text_words = normalized_text.split()
    query_words = normalized_query.split()

    for query_word in query_words:
        for text_word in text_words:
            if query_word in text_word or text_word in query_word:
                return True

    return False


def search_products_python(query_text):
    """Поиск товаров с использованием Python-фильтрации"""
    if not query_text:
        return Product.query.all()

    all_products = Product.query.all()
    matching_products = []
    normalized_query = normalize_text_for_search(query_text)

    for product in all_products:
        # Проверяем все поля товара
        if (advanced_search_in_text(product.name, query_text) or
                advanced_search_in_text(product.article, query_text) or
                advanced_search_in_text(product.short_desc, query_text) or
                advanced_search_in_text(product.full_desc, query_text) or
                (product.brand and advanced_search_in_text(product.brand.name, query_text)) or
                any(advanced_search_in_text(cat.name, query_text) for cat in product.categories)):
            matching_products.append(product)

    return matching_products


# Функции для получения SEO настроек
def get_main_page_seo():
    """Получение SEO для главной страницы"""
    from app.utilities.template_utils import get_seo_meta
    return get_seo_meta('main')


def get_catalog_page_seo(category=None):
    """Получение SEO для страницы каталога"""
    from app.utilities.template_utils import get_seo_meta
    context = {}
    if category:
        context['category_name'] = category.name
        context['category_full_name'] = category.get_full_name()

    return get_seo_meta('catalog', **context)


def get_product_page_seo(product):
    """Получение SEO для страницы товара"""
    from app.utilities.template_utils import get_seo_meta
    return get_seo_meta('product', product.id,
                        product_name=product.name,
                        product_article=product.article,
                        product_short_desc=product.short_desc or '',
                        product_brand=product.brand.name if product.brand else '',
                        product_price=product.price)


def get_news_page_seo(news_item=None):
    """Получение SEO для страницы новостей"""
    from app.utilities.template_utils import get_seo_meta
    context = {}
    if news_item:
        context['news_title'] = news_item.title

    return get_seo_meta('news', news_item.id if news_item else None, **context)


def get_search_page_seo(query, count):
    """Получение SEO для страницы поиска"""
    from app.utilities.template_utils import get_seo_meta
    return get_seo_meta('search', query=query, count=count)


# === Маршруты ===

@main.route('/')
def index():
    """Главная страница"""
    # Получаем последние новости
    latest_news = News.query.order_by(News.created_at.desc()).limit(3).all()
    # Получаем последние товары (последние 6 добавленных)
    latest_products = Product.query.order_by(Product.created_at.desc()).limit(6).all()

    # Получаем SEO настройки
    seo = get_main_page_seo()

    return render_template('index.html',
                           news=latest_news,
                           products=latest_products,
                           seo=seo)


# Маршрут для категорий по slug
@main.route('/catalog/<path:category_slug>')
def catalog_by_slug(category_slug):
    """Каталог по slug"""
    # Разбиваем slug на части для поддержки вложенных категорий
    slug_parts = category_slug.split('/')

    # Находим последнюю категорию в пути
    category = None

    for i, slug_part in enumerate(slug_parts):
        if i == 0:
            # Ищем родительскую категорию
            category = Category.query.filter_by(slug=slug_part, parent_id=None).first()
        else:
            # Ищем подкатегорию
            if category:
                category = Category.query.filter_by(slug=slug_part, parent_id=category.id).first()
            else:
                break

    if not category:
        abort(404)

    page = request.args.get('page', 1, type=int)
    price_from = request.args.get('price_from', type=float)
    price_to = request.args.get('price_to', type=float)

    # Получаем бренды из запроса
    brand_filters = []
    for key, value in request.args.items():
        if key.startswith('brand_') and value == 'on':
            try:
                brand_id = int(key.split('_')[1])
                brand_filters.append(brand_id)
            except (ValueError, IndexError):
                continue

    # Фильтрация по категории
    query = Product.query.join(product_category).join(Category).filter(Category.id == category.id)

    # Фильтрация по цене
    if price_from is not None:
        query = query.filter(Product.price >= price_from)
    if price_to is not None:
        query = query.filter(Product.price <= price_to)

    # Фильтрация по брендам
    if brand_filters:
        query = query.filter(Product.brand_id.in_(brand_filters))

    products = query.paginate(page=page, per_page=9)

    # Получаем категории и бренды для фильтрации
    parent_categories = Category.query.filter_by(parent_id=None).all()
    all_categories = Category.query.all()
    brands = Brand.query.all()

    # Получаем SEO настройки
    seo = get_catalog_page_seo(category)

    return render_template('catalog.html',
                           products=products,
                           parent_categories=parent_categories,
                           all_categories=all_categories,
                           current_category=category.id,
                           brands=brands,
                           category=category,
                           seo=seo)


# Маршрут для товаров по slug
@main.route('/product/<string:product_slug>')
def product_detail(product_slug):
    """Страница товара"""
    from app.forms.cart_forms import AddToCartForm
    product = Product.query.filter_by(slug=product_slug).first_or_404()
    form = AddToCartForm()

    # Получаем SEO настройки
    seo = get_product_page_seo(product)

    return render_template('product_detail.html', product=product, form=form, seo=seo)


# Маршрут для новостей по slug
@main.route('/news/<string:news_slug>')
def news_item(news_slug):
    """Страница новости"""
    news_item = News.query.filter_by(slug=news_slug).first_or_404()

    # Получаем последние новости для сайдбара (исключая текущую новость)
    latest_news_sidebar = News.query.filter(News.id != news_item.id).order_by(News.created_at.desc()).limit(3).all()
    # Получаем последние товары для сайдбара
    latest_products_sidebar = Product.query.order_by(Product.created_at.desc()).limit(3).all()

    # Получаем SEO настройки
    seo = get_news_page_seo(news_item)

    return render_template('news_item.html',
                           news=news_item,
                           seo=seo,
                           latest_news_sidebar=latest_news_sidebar,
                           latest_products_sidebar=latest_products_sidebar)


# Основной маршрут каталога
@main.route('/catalog')
def catalog():
    """Каталог (общий)"""
    page = request.args.get('page', 1, type=int)
    category_id = request.args.get('category', type=int)
    price_from = request.args.get('price_from', type=float)
    price_to = request.args.get('price_to', type=float)

    # Получаем бренды из запроса
    brand_filters = []
    for key, value in request.args.items():
        if key.startswith('brand_') and value == 'on':
            try:
                brand_id = int(key.split('_')[1])
                brand_filters.append(brand_id)
            except (ValueError, IndexError):
                continue

    # Базовый запрос
    query = Product.query

    # Фильтрация по категории
    if category_id:
        category = Category.query.get_or_404(category_id)
        if category.is_parent():
            # Если родительская, ищем по всем подкатегориям
            subcategory_ids = [child.id for child in category.children]
            subcategory_ids.append(category_id)
            query = query.join(product_category).join(Category).filter(Category.id.in_(subcategory_ids))
        else:
            # Если подкатегория, ищем только по ней
            query = query.join(product_category).join(Category).filter(Category.id == category_id)

    # Фильтрация по цене
    if price_from is not None:
        query = query.filter(Product.price >= price_from)
    if price_to is not None:
        query = query.filter(Product.price <= price_to)

    # Фильтрация по брендам
    if brand_filters:
        query = query.filter(Product.brand_id.in_(brand_filters))

    products = query.paginate(page=page, per_page=9)

    # Получаем категории и бренды для фильтрации
    parent_categories = Category.query.filter_by(parent_id=None).all()
    all_categories = Category.query.all()
    brands = Brand.query.all()

    # Получаем SEO настройки
    seo = get_catalog_page_seo()

    return render_template('catalog.html',
                           products=products,
                           parent_categories=parent_categories,
                           all_categories=all_categories,
                           current_category=category_id,
                           brands=brands,
                           seo=seo)


# Страница новостей
@main.route('/news')
def news():
    """Страница новостей"""
    page = request.args.get('page', 1, type=int)
    news_items = News.query.order_by(News.created_at.desc()).paginate(page=page, per_page=5)

    # Получаем последние новости для сайдбара
    latest_news_sidebar = News.query.order_by(News.created_at.desc()).limit(3).all()
    # Получаем последние товары для сайдбара
    latest_products_sidebar = Product.query.order_by(Product.created_at.desc()).limit(3).all()

    # Получаем SEO настройки
    seo = get_news_page_seo()

    return render_template('news.html',
                           news=news_items,
                           seo=seo,
                           latest_news_sidebar=latest_news_sidebar,
                           latest_products_sidebar=latest_products_sidebar)


# Поиск
@main.route('/search')
def search():
    """Страница результатов поиска"""
    query_text = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)

    # Получаем все товары и фильтруем в Python
    if query_text:
        all_matching_products = search_products_python(query_text)
    else:
        all_matching_products = Product.query.all()

    # Ручная пагинация
    per_page = 12
    total = len(all_matching_products)
    start = (page - 1) * per_page
    end = start + per_page
    paginated_products = all_matching_products[start:end]

    # Создаем объект пагинации вручную
    class ManualPagination:
        def __init__(self, items, page, per_page, total):
            self.items = items
            self.page = page
            self.per_page = per_page
            self.total = total
            self.pages = (total + per_page - 1) // per_page if per_page > 0 else 0
            self.has_prev = page > 1
            self.has_next = page < self.pages
            self.prev_num = page - 1 if self.has_prev else None
            self.next_num = page + 1 if self.has_next else None

        def iter_pages(self, left_edge=2, left_current=2, right_current=5, right_edge=2):
            last = 0
            for num in range(1, self.pages + 1):
                if num <= left_edge or \
                        (num > self.page - left_current - 1 and num < self.page + right_current) or \
                        num > self.pages - right_edge:
                    if last + 1 != num:
                        yield None
                    yield num
                    last = num

    products = ManualPagination(
        items=paginated_products,
        page=page,
        per_page=per_page,
        total=total
    )

    # Получаем SEO настройки
    seo = get_search_page_seo(query_text, total)

    return render_template('search_results.html',
                           products=products,
                           query=query_text,
                           seo=seo)


# API для автоподсказок поиска
@main.route('/api/search')
def api_search():
    """API для автоподсказок поиска"""
    query_text = request.args.get('q', '').strip()

    if len(query_text) < 2:
        return jsonify([])

    # Используем Python-фильтрацию для автоподсказок
    all_products = Product.query.all()
    matching_products = []
    normalized_query = normalize_text_for_search(query_text)

    for product in all_products:
        # Проверяем название и артикул
        if (advanced_search_in_text(product.name, query_text) or
                advanced_search_in_text(product.article, query_text)):
            matching_products.append(product)

            # Ограничиваем до 8 результатов
            if len(matching_products) >= 8:
                break

    # Формируем результаты
    results = []
    for product in matching_products:
        # Используем правильный путь к placeholder
        if product.image_url:
            image_url = product.image_url
        else:
            image_url = url_for('static', filename='images/placeholder.png')

        results.append({
            'id': product.id,
            'name': product.name,
            'article': product.article,
            'price': float(product.price),
            'image_url': image_url,
            'url': url_for('main.product_detail', product_slug=product.slug)
        })

    return jsonify(results)