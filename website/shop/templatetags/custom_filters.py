from django import template

register = template.Library()


# пользовательский фильтр шаблона, чтобы получить значение рейтинга из словаря по ключу
@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)
