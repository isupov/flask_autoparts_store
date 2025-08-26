from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, FloatField, IntegerField, SelectField, SubmitField
from wtforms.validators import DataRequired, NumberRange
from flask_wtf.file import FileField, FileAllowed

class ProductForm(FlaskForm):
    name = StringField('Название товара', validators=[DataRequired()])
    article = StringField('Артикул', validators=[DataRequired()])
    short_desc = TextAreaField('Краткое описание')
    full_desc = TextAreaField('Полное описание')
    price = FloatField('Цена', validators=[DataRequired(), NumberRange(min=0)])
    stock = IntegerField('Количество на складе', validators=[DataRequired(), NumberRange(min=0)])
    brand_id = SelectField('Бренд', coerce=int, validators=[DataRequired()])
    country_id = SelectField('Страна производства', coerce=int, validators=[DataRequired()])
    category_ids = SelectField('Категории', coerce=int, validators=[DataRequired()])
    image = FileField('Изображение товара', validators=[FileAllowed(['jpg', 'png', 'jpeg', 'gif'], 'Только изображения!')])
    submit = SubmitField('Сохранить')