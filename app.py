from app import create_app, db
from app.models import User, Category, Brand, Country, Product, CartItem, News, product_category

app = create_app()

# Создаем контекст приложения для shell
@app.shell_context_processor
def make_shell_context():
    return {
        'db': db,
        'User': User,
        'Category': Category,
        'Brand': Brand,
        'Country': Country,
        'Product': Product,
        'CartItem': CartItem,
        'News': News,
        'product_category': product_category
    }

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5002, debug=True)
    with app.app_context():
        db.create_all()
    app.run(debug=True)