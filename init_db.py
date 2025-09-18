from app import create_app, db
from app.models import User, Category, Brand, Country, Product, News, Setting, SeoMeta
from app.utilities.helpers import transliterate
import os


def init_database():
    app = create_app()
    with app.app_context():
        # Создаем все таблицы
        db.create_all()

        # Проверяем, есть ли уже данные
        if User.query.first() is None:
            print("Инициализация базы данных...")

            # Создаем администратора
            admin = User(username='admin', email='admin@example.com', is_admin=True)
            admin.set_password('admin123')
            db.session.add(admin)

            # Создаем бренды с slug'ами
            brands_data = [
                ('Bosch', 'bosch'),
                ('Continental', 'continental'),
                ('Michelin', 'michelin'),
                ('Castrol', 'castrol'),
                ('Mobil', 'mobil'),
                ('Shell', 'shell'),
                ('Motul', 'motul')
            ]
            brands = []
            for brand_name, brand_slug in brands_data:
                brand = Brand(name=brand_name, slug=brand_slug)
                db.session.add(brand)
                brands.append(brand)

            # Создаем страны
            countries_data = ['Германия', 'Франция', 'Япония', 'США', 'Китай', 'Россия', 'Южная Корея']
            countries = []
            for country_name in countries_data:
                country = Country(name=country_name)
                db.session.add(country)
                countries.append(country)

            # Создаем родительские категории с slug'ами
            parent_categories_data = [
                ('Фильтры', 'filtry'),
                ('Автокосметика', 'avtokosmetika'),
                ('Моторные масла', 'motor-masla'),
                ('Тормозная система', 'tormoznaya-sistema'),
                ('Подвеска', 'podveska')
            ]

            parent_categories = {}
            for name, slug in parent_categories_data:
                category = Category(name=name, slug=slug)
                db.session.add(category)
                db.session.flush()
                parent_categories[name] = category

            # Создаем подкатегории
            subcategories_data = [
                ('Масляные фильтры', 'maslyanye-filtry', parent_categories['Фильтры'].id),
                ('Воздушные фильтры', 'vozdushnye-filtry', parent_categories['Фильтры'].id),
                ('Топливные фильтры', 'toplivnye-filtry', parent_categories['Фильтры'].id),
                ('Очистители салона', 'ochistiteli-salona', parent_categories['Автокосметика'].id),
                ('Полироли', 'polirol', parent_categories['Автокосметика'].id),
                ('Шампуни для авто', 'shampuni-dlya-avto', parent_categories['Автокосметика'].id),
                ('Синтетические масла', 'sinteticheskie-masla', parent_categories['Моторные масла'].id),
                ('Полусинтетические масла', 'polusinteticheskie-masla', parent_categories['Моторные масла'].id),
                ('Минеральные масла', 'mineralnye-masla', parent_categories['Моторные масла'].id)
            ]

            subcategories = {}
            for name, slug, parent_id in subcategories_data:
                category = Category(name=name, slug=slug, parent_id=parent_id)
                db.session.add(category)
                db.session.flush()
                subcategories[name] = category

            # Создаем тестовые новости с slug'ами
            news_data = [
                {
                    'title': 'Новые поступления запчастей',
                    'slug': 'novye-postupleniya-zapchastei',
                    'content': '<p>Мы пополнили склад новыми запчастями для автомобилей различных марок. В наличии фильтры, масла и другие автозапчасти от ведущих производителей.</p><p>Специальные цены на товары месяца!</p>'
                },
                {
                    'title': 'Скидки на зимние шины',
                    'slug': 'skidki-na-zimnie-shiny',
                    'content': '<p>Специальное предложение на зимние шины Continental и Michelin до конца месяца. Скидки до 30% на весь ассортимент!</p><p>Успейте приобрести по выгодным ценам!</p>'
                },
                {
                    'title': 'Расширение ассортимента автокосметики',
                    'slug': 'rasshirenie-assortimenta-avtokosmetiki',
                    'content': '<p>Новый раздел автокосметики уже открыт! В продаже очистители салона, полироли, шампуни и многое другое.</p><p>Профессиональные средства по уходу за автомобилем по доступным ценам.</p>'
                }
            ]

            for news_item in news_data:
                news = News(
                    title=news_item['title'],
                    slug=news_item['slug'],
                    content=news_item['content']
                )
                db.session.add(news)

            db.session.commit()

            # Создаем тестовые товары с slug'ами
            products_data = [
                {
                    'name': 'Воздушный фильтр Bosch',
                    'slug': '1-vozdushnyi-filtr-bosch',  # Будет обновлен при создании
                    'article': 'AF-12345',
                    'short_desc': 'Высококачественный воздушный фильтр для автомобилей',
                    'full_desc': '<p>Профессиональный воздушный фильтр Bosch обеспечивает отличную фильтрацию воздуха, поступающего в двигатель.</p><p><strong>Характеристики:</strong></p><ul><li>Высокая степень фильтрации</li><li>Долговечность</li><li>Совместимость с большинством автомобилей</li></ul>',
                    'price': 1299.99,
                    'stock': 50,
                    'brand_id': brands[0].id,  # Bosch
                    'country_id': countries[0].id,  # Германия
                },
                {
                    'name': 'Масляный фильтр Mann-Filter',
                    'slug': '2-maslyanyi-filtr-mann-filter',
                    'article': 'OF-67890',
                    'short_desc': 'Фильтр масляный высокого качества',
                    'full_desc': '<p>Масляный фильтр Mann-Filter обеспечивает надежную очистку масла и продлевает срок службы двигателя.</p><p><strong>Преимущества:</strong></p><ul><li>Высокая пропускная способность</li><li>Надежная герметизация</li><li>Долгий срок службы</li></ul>',
                    'price': 899.50,
                    'stock': 30,
                    'brand_id': brands[1].id,  # Continental
                    'country_id': countries[1].id,  # Франция
                },
                {
                    'name': 'Очиститель салона Meguiar\'s',
                    'slug': '3-ochistitel-salona-meguiars',
                    'article': 'CL-54321',
                    'short_desc': 'Универсальный очиститель для салона автомобиля',
                    'full_desc': '<p>Очиститель салона Meguiar\'s эффективно удаляет загрязнения с различных поверхностей салона автомобиля.</p><p><strong>Подходит для:</strong></p><ul><li>Пластиковых поверхностей</li><li>Резиновых вставок</li><li>Тканевой обивки</li><li>Ковровых покрытий</li></ul>',
                    'price': 1599.00,
                    'stock': 25,
                    'brand_id': brands[6].id,  # Motul
                    'country_id': countries[3].id,  # США
                },
                {
                    'name': 'Синтетическое масло Castrol',
                    'slug': '4-sinteticheskoe-maslo-castrol',
                    'article': 'MO-98765',
                    'short_desc': 'Синтетическое моторное масло премиум класса',
                    'full_desc': '<p>Синтетическое моторное масло Castrol обеспечивает превосходную защиту двигателя в любых условиях эксплуатации.</p><p><strong>Характеристики:</strong></p><ul><li>Вязкость 5W-30</li><li>Объем 5 литров</li><li>Соответствует стандартам API SN</li><li>Экономия топлива</li></ul>',
                    'price': 3299.99,
                    'stock': 40,
                    'brand_id': brands[3].id,  # Castrol
                    'country_id': countries[0].id,  # Германия
                }
            ]

            # Создаем товары и связываем их с категориями
            for i, product_data in enumerate(products_data):
                product = Product(**product_data)
                db.session.add(product)
                db.session.flush()

                # Обновляем slug с правильным ID
                product.slug = f"{product.id}-{transliterate(product.name)}"

                # Связываем с соответствующими категориями
                if i == 0:  # Воздушный фильтр
                    product.categories.append(subcategories['Воздушные фильтры'])
                elif i == 1:  # Масляный фильтр
                    product.categories.append(subcategories['Масляные фильтры'])
                elif i == 2:  # Очиститель салона
                    product.categories.append(subcategories['Очистители салона'])
                elif i == 3:  # Синтетическое масло
                    product.categories.append(subcategories['Синтетические масла'])

            db.session.commit()

            # Создаем начальные настройки сайта
            settings_data = [
                ('site_name', 'Автозапчасти Shop', 'Название сайта'),
                ('site_description', 'Интернет-магазин автозапчастей с широким ассортиментом по выгодным ценам',
                 'Описание сайта'),
                ('site_keywords', 'автозапчасти, запчасти для автомобиля, фильтры, масла, тормозные колодки',
                 'Ключевые слова сайта'),
                ('main_page_title', 'Автозапчасти Shop - Качественные автозапчасти по выгодным ценам',
                 'Title главной страницы'),
                ('main_page_description',
                 'Купить автозапчасти в интернет-магазине Автозапчасти Shop. Широкий ассортимент, выгодные цены, быстрая доставка.',
                 'Description главной страницы'),
                ('main_page_heading', 'Добро пожаловать в Автозапчасти Shop!', 'Заголовок на главной странице'),
                ('main_page_subheading', 'Широкий ассортимент автозапчастей по выгодным ценам',
                 'Подзаголовок на главной странице'),
                ('contact_email', 'info@auto-parts-shop.ru', 'Email для контактов'),
                ('contact_phone', '+7 (495) 123-45-67', 'Телефон для контактов'),
                ('address', 'г. Москва, ул. Автозапчастная, д. 15', 'Адрес магазина')
            ]

            for key, value, description in settings_data:
                existing_setting = Setting.query.filter_by(key=key).first()
                if not existing_setting:
                    setting = Setting(key=key, value=value, description=description)
                    db.session.add(setting)

            # Создаем SEO настройки по умолчанию
            seo_defaults = [
                ('main', None, 'Автозапчасти Shop - Качественные автозапчасти',
                 'Купить автозапчасти в интернет-магазине Автозапчасти Shop. Широкий ассортимент, выгодные цены, быстрая доставка.',
                 'автозапчасти, запчасти для автомобиля, интернет-магазин, выгодные цены', 'index, follow'),
                ('catalog', None, 'Каталог автозапчастей - Автозапчасти Shop',
                 'Широкий каталог автозапчастей: фильтры, масла, тормозные системы, подвеска. Выгодные цены, быстрая доставка.',
                 'каталог автозапчастей, фильтры, масла, тормозные колодки', 'index, follow'),
                ('product', None, '{product_name} - купить в интернет-магазине', '{product_short_desc}',
                 '{product_name}, {product_article}, купить автозапчасти', 'index, follow'),
                ('news', None, 'Новости автозапчастей - Автозапчасти Shop',
                 'Последние новости из мира автозапчастей, акции, новинки, советы по уходу за автомобилем.',
                 'новости автозапчастей, акции, новинки', 'index, follow'),
                ('search', None, 'Поиск автозапчастей - {query}',
                 'Результаты поиска по запросу: {query}. Найдено {count} товаров.', 'поиск автозапчастей, {query}',
                 'index, follow')
            ]

            for page_type, page_id, title, description, keywords, robots in seo_defaults:
                existing_seo = SeoMeta.query.filter_by(page_type=page_type, page_id=page_id).first()
                if not existing_seo:
                    seo = SeoMeta(
                        page_type=page_type,
                        page_id=page_id,
                        title=title,
                        description=description,
                        keywords=keywords,
                        robots=robots
                    )
                    db.session.add(seo)

            db.session.commit()

            print("✅ База данных инициализирована успешно!")
            print("📁 Папки для загрузок созданы")
            print("👤 Администратор: логин 'admin', пароль 'admin123'")
            print("📊 Создано:")
            print(f"   - {User.query.count()} пользователей")
            print(f"   - {Category.query.count()} категорий")
            print(f"   - {Brand.query.count()} брендов")
            print(f"   - {Country.query.count()} стран")
            print(f"   - {Product.query.count()} товаров")
            print(f"   - {News.query.count()} новостей")
            print("   - Настройки сайта")
            print("   - SEO настройки")
        else:
            print("⚠️  База данных уже содержит данные")


if __name__ == '__main__':
    init_database()