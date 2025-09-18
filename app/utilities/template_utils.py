from app.models import Setting, SeoMeta


def get_site_setting(key, default=None):
    """Получение настройки сайта для шаблонов"""
    setting = Setting.query.filter_by(key=key).first()
    return setting.value if setting else default


def get_seo_meta(page_type, page_id=None, **context):
    """
    Получение SEO мета-тегов для страницы
    """
    seo = SeoMeta.get_for_page(page_type, page_id)

    if not seo:
        # Возвращаем дефолтные значения
        return {
            'title': get_site_setting('site_name', 'Автозапчасти Shop'),
            'description': get_site_setting('site_description', ''),
            'keywords': get_site_setting('site_keywords', ''),
            'robots': 'index, follow'
        }

    # Подставляем значения из контекста
    title = seo.title or ''
    description = seo.description or ''
    keywords = seo.keywords or ''

    # Заменяем плейсхолдеры на реальные значения
    for key, value in context.items():
        if value:
            title = title.replace(f'{{{key}}}', str(value))
            description = description.replace(f'{{{key}}}', str(value))
            keywords = keywords.replace(f'{{{key}}}', str(value))

    return {
        'title': title,
        'description': description,
        'keywords': keywords,
        'robots': seo.robots or 'index, follow'
    }


def get_main_page_seo():
    """Получение SEO для главной страницы"""
    return get_seo_meta('main')


def get_catalog_page_seo(category=None):
    """Получение SEO для страницы каталога"""
    context = {}
    if category:
        context['category_name'] = category.name
        context['category_full_name'] = category.get_full_name()

    return get_seo_meta('catalog', **context)


def get_product_page_seo(product):
    """Получение SEO для страницы товара"""
    return get_seo_meta('product', product.id,
                        product_name=product.name,
                        product_article=product.article,
                        product_short_desc=product.short_desc or '',
                        product_brand=product.brand.name if product.brand else '',
                        product_price=product.price)


def get_news_page_seo(news_item=None):
    """Получение SEO для страницы новостей"""
    context = {}
    if news_item:
        context['news_title'] = news_item.title

    return get_seo_meta('news', news_item.id if news_item else None, **context)


def get_search_page_seo(query, count):
    """Получение SEO для страницы поиска"""
    return get_seo_meta('search', query=query, count=count)


# Экспортируем функции для контекста Jinja2
template_functions = {
    'get_site_setting': get_site_setting,
    'get_seo_meta': get_seo_meta,
    'get_main_page_seo': get_main_page_seo,
    'get_catalog_page_seo': get_catalog_page_seo,
    'get_product_page_seo': get_product_page_seo,
    'get_news_page_seo': get_news_page_seo,
    'get_search_page_seo': get_search_page_seo
}