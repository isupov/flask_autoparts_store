from flask import Blueprint, render_template, request, jsonify, url_for
from flask_login import current_user
from app.models import Product, News, Category, product_category, Brand
from sqlalchemy import or_  # Добавляем импорт or_

main = Blueprint('main', __name__)


@main.route('/')
def index():
    # Получаем последние новости
    latest_news = News.query.order_by(News.created_at.desc()).limit(3).all()
    # Получаем последние товары (последние 6 добавленных)
    latest_products = Product.query.order_by(Product.created_at.desc()).limit(6).all()
    return render_template('index.html', news=latest_news, products=latest_products)


@main.route('/catalog')
def catalog():
    page = request.args.get('page', 1, type=int)
    category_id = request.args.get('category', type=int)
    price_from = request.args.get('price_from', type=float)
    price_to = request.args.get('price_to', type=float)

    # Получаем все бренды из запроса
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

    return render_template('catalog.html',
                           products=products,
                           parent_categories=parent_categories,
                           all_categories=all_categories,
                           current_category=category_id,
                           brands=brands)

@main.route('/news')
def news():
    page = request.args.get('page', 1, type=int)
    news_items = News.query.order_by(News.created_at.desc()).paginate(page=page, per_page=5)
    return render_template('news.html', news=news_items)


@main.route('/news/<int:news_id>')
def news_item(news_id):
    news_item = News.query.get_or_404(news_id)
    return render_template('news_item.html', news=news_item)


@main.route('/product/<int:product_id>')
def product_detail(product_id):
    from app.forms.cart_forms import AddToCartForm
    product = Product.query.get_or_404(product_id)
    form = AddToCartForm()
    return render_template('product_detail.html', product=product, form=form)


@main.route('/search')
def search():
    """Страница результатов поиска с улучшенным поиском"""
    query = request.args.get('q', '').strip()
    page = request.args.get('page', 1, type=int)

    if query:
        # Регистронезависимый поиск по названию и артикулу
        products = Product.query.filter(
            or_(
                Product.name.ilike(f'%{query}%'),
                Product.article.ilike(f'%{query}%')
            )
        ).paginate(page=page, per_page=12)
    else:
        products = Product.query.paginate(page=page, per_page=12)

    return render_template('search_results.html', products=products, query=query)


@main.route('/api/search')
def api_search():
    """API для автоподсказок поиска"""
    query = request.args.get('q', '').strip()

    if len(query) < 2:
        return jsonify([])

    # Ищем товары по названию (регистронезависимый поиск)
    products = Product.query.filter(
        Product.name.ilike(f'%{query}%')
    ).limit(8).all()

    # Формируем результаты
    results = []
    for product in products:
        results.append({
            'id': product.id,
            'name': product.name,
            'article': product.article,
            'price': float(product.price),
            'image_url': product.image_url or '/static/images/placeholder.png',
            'url': url_for('main.product_detail', product_id=product.id)
        })

    return jsonify(results)