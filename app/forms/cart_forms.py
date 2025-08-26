from flask_wtf import FlaskForm
from wtforms import IntegerField, SubmitField
from wtforms.validators import DataRequired, NumberRange

class AddToCartForm(FlaskForm):
    quantity = IntegerField('Количество',
                           validators=[DataRequired(), NumberRange(min=1)],
                           default=1)
    submit = SubmitField('Добавить в корзину')