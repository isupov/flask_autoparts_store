from flask import Blueprint, render_template, request, Response
from app.models import Product, News, Category
from datetime import datetime
import math

sitemap = Blueprint('sitemap', __name__)


@sitemap.route('/sitemap.xml')
def sitemap_xml():
    """Генерация sitemap.xml"""
    # Получаем все страницы для sitemap
    pages = []

    # Основные страницы
    pages.extend([
        {
            'loc': '/',
            'lastmod': datetime.utcnow().strftime('%Y-%m-%d'),
            'changefreq': 'daily',
            'priority': '1.0'
        },
        {
            'loc': '/catalog',
            'lastmod': datetime.utcnow().strftime('%Y-%m-%d'),
            'changefreq': 'weekly',
            'priority': '0.9'
        },
        {
            'loc': '/news',
            'lastmod': datetime.utcnow().strftime('%Y-%m-%d'),
            'changefreq': 'daily',
            'priority': '0.8'
        }
    ])

    # Категории
    categories = Category.query.all()
    for category in categories:
        pages.append({
            'loc': f'/catalog/{category.slug}',
            'lastmod': category.created_at.strftime('%Y-%m-%d') if category.created_at else datetime.utcnow().strftime(
                '%Y-%m-%d'),
            'changefreq': 'weekly',
            'priority': '0.7'
        })

    # Товары
    products = Product.query.all()
    for product in products:
        pages.append({
            'loc': f'/product/{product.slug}',
            'lastmod': product.created_at.strftime('%Y-%m-%d') if product.created_at else datetime.utcnow().strftime(
                '%Y-%m-%d'),
            'changefreq': 'monthly',
            'priority': '0.6'
        })

    # Новости
    news_items = News.query.all()
    for news_item in news_items:
        pages.append({
            'loc': f'/news/{news_item.slug}',
            'lastmod': news_item.created_at.strftime(
                '%Y-%m-%d') if news_item.created_at else datetime.utcnow().strftime('%Y-%m-%d'),
            'changefreq': 'monthly',
            'priority': '0.5'
        })

    # Генерируем XML
    xml_sitemap = render_template('sitemap.xml', pages=pages)

    return Response(xml_sitemap, mimetype='application/xml')