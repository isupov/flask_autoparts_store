from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models import Product, CartItem

cart = Blueprint('cart', __name__)


@cart.route('/cart')
@login_required
def view_cart():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    total = sum(item.product.price * item.quantity for item in cart_items)
    return render_template('cart/view_cart.html', cart_items=cart_items, total=total)


@cart.route('/cart/add/<int:product_id>', methods=['POST'])  # Убедимся, что метод POST разрешен
@login_required
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)

    # Получаем количество из формы
    quantity = int(request.form.get('quantity', 1))

    # Проверяем наличие товара
    if quantity > product.stock:
        flash(f'Недостаточно товара на складе. Доступно: {product.stock} шт.', 'error')
        return redirect(request.referrer or url_for('main.catalog'))

    # Проверяем, есть ли уже такой товар в корзине
    cart_item = CartItem.query.filter_by(
        user_id=current_user.id,
        product_id=product_id
    ).first()

    if cart_item:
        # Проверяем общее количество
        new_quantity = cart_item.quantity + quantity
        if new_quantity > product.stock:
            flash(f'Недостаточно товара на складе. Максимальное количество: {product.stock} шт.', 'error')
            return redirect(request.referrer or url_for('main.catalog'))
        cart_item.quantity = new_quantity
    else:
        # Создаем новую запись в корзине
        cart_item = CartItem(
            user_id=current_user.id,
            product_id=product_id,
            quantity=quantity
        )
        db.session.add(cart_item)

    db.session.commit()
    flash(f'Товар "{product.name}" добавлен в корзину!', 'success')

    # Возвращаем пользователя на ту же страницу
    return redirect(request.referrer or url_for('main.catalog'))


@cart.route('/cart/update/<int:item_id>', methods=['POST'])
@login_required
def update_cart_item(item_id):
    cart_item = CartItem.query.filter_by(
        id=item_id,
        user_id=current_user.id
    ).first_or_404()

    quantity = request.form.get('quantity', type=int)

    if quantity is None or quantity < 1:
        flash('Некорректное количество', 'error')
        return redirect(url_for('cart.view_cart'))

    if quantity > cart_item.product.stock:
        flash(f'Недостаточно товара на складе. Доступно: {cart_item.product.stock} шт.', 'error')
        return redirect(url_for('cart.view_cart'))

    cart_item.quantity = quantity
    db.session.commit()
    flash('Количество обновлено', 'success')

    return redirect(url_for('cart.view_cart'))


@cart.route('/cart/remove/<int:item_id>')
@login_required
def remove_from_cart(item_id):
    cart_item = CartItem.query.filter_by(
        id=item_id,
        user_id=current_user.id
    ).first_or_404()

    db.session.delete(cart_item)
    db.session.commit()
    flash('Товар удален из корзины', 'success')

    return redirect(url_for('cart.view_cart'))