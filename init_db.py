from app import create_app, db
from app.models import User, Category, Brand, Country, Product, News
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
            admin.set_password('admin123')  # Теперь метод есть
            db.session.add(admin)

            # Создаем бренды
            brands_data = ['Bosch', 'Continental', 'Michelin', 'Castrol', 'Mobil', 'Shell', 'Motul']
            brands = []
            for brand_name in brands_data:
                brand = Brand(name=brand_name)
                db.session.add(brand)
                brands.append(brand)

            # Создаем страны
            countries_data = ['Германия', 'Франция', 'Япония', 'США', 'Китай', 'Россия', 'Южная Корея']
            countries = []
            for country_name in countries_data:
                country = Country(name=country_name)
                db.session.add(country)
                countries.append(country)

            # Создаем родительские категории
            parent_categories_data = [
                ('Фильтры', None),
                ('Автокосметика', None),
                ('Моторные масла', None),
                ('Тормозная система', None),
                ('Подвеска', None)
            ]

            parent_categories = {}
            for name, parent_id in parent_categories_data:
                category = Category(name=name, parent_id=parent_id)
                db.session.add(category)
                db.session.flush()  # Чтобы получить ID
                parent_categories[name] = category

            # Создаем подкатегории
            subcategories_data = [
                ('Масляные фильтры', parent_categories['Фильтры'].id),
                ('Воздушные фильтры', parent_categories['Фильтры'].id),
                ('Топливные фильтры', parent_categories['Фильтры'].id),
                ('Очистители салона', parent_categories['Автокосметика'].id),
                ('Полироли', parent_categories['Автокосметика'].id),
                ('Шампуни для авто', parent_categories['Автокосметика'].id),
                ('Синтетические масла', parent_categories['Моторные масла'].id),
                ('Полусинтетические масла', parent_categories['Моторные масла'].id),
                ('Минеральные масла', parent_categories['Моторные масла'].id)
            ]

            subcategories = {}
            for name, parent_id in subcategories_data:
                category = Category(name=name, parent_id=parent_id)
                db.session.add(category)
                db.session.flush()
                subcategories[name] = category

            # Создаем тестовые новости
            news_data = [
                {
                    'title': 'Новые поступления запчастей',
                    'content': '<p>Мы пополнили склад новыми запчастями для автомобилей различных марок. В наличии фильтры, масла и другие автозапчасти от ведущих производителей.</p><p>Специальные цены на товары месяца!</p>'
                },
                {
                    'title': 'Скидки на зимние шины',
                    'content': '<p>Специальное предложение на зимние шины Continental и Michelin до конца месяца. Скидки до 30% на весь ассортимент!</p><p>Успейте приобрести по выгодным ценам!</p>'
                },
                {
                    'title': 'Расширение ассортимента автокосметики',
                    'content': '<p>Новый раздел автокосметики уже открыт! В продаже очистители салона, полироли, шампуни и многое другое.</p><p>Профессиональные средства по уходу за автомобилем по доступным ценам.</p>'
                }
            ]

            for news_item in news_data:
                news = News(title=news_item['title'], content=news_item['content'])
                db.session.add(news)

            db.session.commit()

            # Создаем тестовые товары
            products_data = [
                {
                    'name': 'Воздушный фильтр Bosch',
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

            print("✅ База данных инициализирована успешно!")
            print("👤 Администратор: логин 'admin', пароль 'admin123'")
            print("📊 Создано:")
            print(f"   - {User.query.count()} пользователей")
            print(f"   - {Category.query.count()} категорий")
            print(f"   - {Brand.query.count()} брендов")
            print(f"   - {Country.query.count()} стран")
            print(f"   - {Product.query.count()} товаров")
            print(f"   - {News.query.count()} новостей")
        else:
            print("⚠️  База данных уже содержит данные")


if __name__ == '__main__':
    init_database()