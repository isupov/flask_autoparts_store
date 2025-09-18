from flask import Blueprint, render_template, request, Response

robots = Blueprint('robots', __name__)

@robots.route('/robots.txt')
def robots_txt():
    """Генерация robots.txt"""
    robots_content = render_template('robots.txt')
    return Response(robots_content, mimetype='text/plain')