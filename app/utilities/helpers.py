import re
import os
import uuid
from PIL import Image
from app.models import Setting, SeoMeta


def transliterate(text):
    """
    Транслитерация кириллического текста в латиницу
    """
    if not text:
        return ""

    # Ручная транслитерация
    transliterated = text

    # Словарь для ручной транслитерации
    translit_dict = {
        'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
        'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
        'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
        'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
        'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
        'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'Yo',
        'Ж': 'Zh', 'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M',
        'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U',
        'Ф': 'F', 'Х': 'H', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Sch',
        'Ъ': '', 'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya'
    }

    for cyrillic, latin in translit_dict.items():
        transliterated = transliterated.replace(cyrillic, latin)

    # Оставляем только буквы, цифры, дефисы и подчеркивания
    # Заменяем пробелы на дефисы
    transliterated = re.sub(r'\s+', '-', transliterated)
    # Удаляем недопустимые символы
    transliterated = re.sub(r'[^a-zA-Z0-9\-_]', '', transliterated)
    # Убираем множественные дефисы
    transliterated = re.sub(r'-+', '-', transliterated)
    # Убираем дефисы в начале и конце
    transliterated = transliterated.strip('-')
    # Приводим к нижнему регистру
    transliterated = transliterated.lower()

    # Если результат пустой, используем slug
    if not transliterated:
        transliterated = "item"

    return transliterated


def generate_slug(text, existing_slugs=None):
    """
    Генерация уникального slug с учетом существующих
    """
    base_slug = transliterate(text)

    if not existing_slugs:
        return base_slug

    # Если slug уже существует, добавляем суффикс
    counter = 1
    slug = base_slug
    while slug in existing_slugs:
        slug = f"{base_slug}-{counter}"
        counter += 1

    return slug


def create_upload_directories(app):
    """
    Создание необходимых директорий для загрузок
    """
    # Создаем все необходимые папки
    for folder_type, folder_path in app.config['UPLOAD_FOLDERS'].items():
        os.makedirs(folder_path, exist_ok=True)
        print(f"Created directory: {folder_path}")


def save_product_image(form_picture, product_name, product_id, app):
    """
    Сохранение изображения товара с правильной структурой
    """
    # Создаем папку если её нет
    product_upload_folder = app.config['UPLOAD_FOLDERS']['products']

    # Получаем первую букву названия товара для структуры папок
    first_letter = transliterate(product_name[:1]).lower() if product_name else '0'
    letter_folder = os.path.join(product_upload_folder, first_letter)
    os.makedirs(letter_folder, exist_ok=True)

    # Генерируем имя файла
    random_hex = uuid.uuid4().hex
    transliterated_name = transliterate(product_name)
    _, f_ext = os.path.splitext(form_picture.filename)

    # Основное изображение
    main_filename = f"{product_id}_{transliterated_name}_{random_hex}{f_ext}"
    main_path = os.path.join(letter_folder, main_filename)

    # Миниатюра
    thumbnail_filename = f"{product_id}_{transliterated_name}_{random_hex}_thumb{f_ext}"
    thumbnail_path = os.path.join(letter_folder, thumbnail_filename)

    # Оптимизируем основное изображение (800x800)
    output_size = (800, 800)
    img = Image.open(form_picture)
    img.thumbnail(output_size)
    img.save(main_path)

    # Создаем миниатюру (300x300)
    thumbnail_size = (300, 300)
    img_thumb = Image.open(form_picture)

    # Преобразуем в RGB если нужно (для PNG с прозрачностью)
    if img_thumb.mode in ('RGBA', 'LA', 'P'):
        img_thumb = img_thumb.convert('RGB')

    # Создаем квадратную миниатюру с обрезкой по центру
    img_thumb.thumbnail(thumbnail_size, Image.Resampling.LANCZOS)

    # Если изображение не квадратное, обрезаем до квадрата
    if img_thumb.size[0] != img_thumb.size[1]:
        # Находим меньшую сторону
        min_side = min(img_thumb.size)
        # Обрезаем до квадрата по центру
        left = (img_thumb.size[0] - min_side) // 2
        top = (img_thumb.size[1] - min_side) // 2
        right = left + min_side
        bottom = top + min_side
        img_thumb = img_thumb.crop((left, top, right, bottom))

    img_thumb = img_thumb.resize(thumbnail_size, Image.Resampling.LANCZOS)
    img_thumb.save(thumbnail_path)

    # Возвращаем относительные пути для сохранения в базу данных
    relative_main_path = f"/static/uploads/products/{first_letter}/{main_filename}"
    relative_thumbnail_path = f"/static/uploads/products/{first_letter}/{thumbnail_filename}"

    return relative_main_path, relative_thumbnail_path


def save_brand_image(form_picture, brand_name, brand_id, app):
    """
    Сохранение изображения бренда
    """
    brand_upload_folder = app.config['UPLOAD_FOLDERS']['brands']
    os.makedirs(brand_upload_folder, exist_ok=True)

    random_hex = uuid.uuid4().hex
    transliterated_name = transliterate(brand_name)
    _, f_ext = os.path.splitext(form_picture.filename)

    filename = f"{brand_id}_{transliterated_name}_{random_hex}{f_ext}"
    file_path = os.path.join(brand_upload_folder, filename)

    # Оптимизируем изображение (400x400 для брендов)
    output_size = (400, 400)
    img = Image.open(form_picture)
    img.thumbnail(output_size)
    img.save(file_path)

    relative_path = f"/static/uploads/brands/{filename}"
    return relative_path


def save_category_image(form_picture, category_name, category_id, app):
    """
    Сохранение изображения категории
    """
    category_upload_folder = app.config['UPLOAD_FOLDERS']['categories']
    os.makedirs(category_upload_folder, exist_ok=True)

    random_hex = uuid.uuid4().hex
    transliterated_name = transliterate(category_name)
    _, f_ext = os.path.splitext(form_picture.filename)

    filename = f"{category_id}_{transliterated_name}_{random_hex}{f_ext}"
    file_path = os.path.join(category_upload_folder, filename)

    # Оптимизируем изображение (600x400 для категорий)
    output_size = (600, 400)
    img = Image.open(form_picture)
    img.thumbnail(output_size)
    img.save(file_path)

    relative_path = f"/static/uploads/categories/{filename}"
    return relative_path


def save_news_image(form_picture, news_title, news_id, app):
    """
    Сохранение изображения новости
    """
    news_upload_folder = app.config['UPLOAD_FOLDERS']['news']
    os.makedirs(news_upload_folder, exist_ok=True)

    random_hex = uuid.uuid4().hex
    transliterated_title = transliterate(news_title)
    _, f_ext = os.path.splitext(form_picture.filename)

    filename = f"{news_id}_{transliterated_title}_{random_hex}{f_ext}"
    file_path = os.path.join(news_upload_folder, filename)

    # Оптимизируем изображение (800x600 для новостей)
    output_size = (800, 600)
    img = Image.open(form_picture)
    img.thumbnail(output_size)
    img.save(file_path)

    relative_path = f"/static/uploads/news/{filename}"
    return relative_path