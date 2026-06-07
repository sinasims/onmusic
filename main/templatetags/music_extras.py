import json
from django import template
from django.conf import settings
import jdatetime

register = template.Library()


@register.filter
def price_format(value):
    try:
        return f'{int(value):,} تومان'
    except (ValueError, TypeError):
        return '۰ تومان'


@register.filter
def to_json(value):
    return json.dumps(value, ensure_ascii=False)


@register.filter
def get_range(value):
    return range(value)


@register.filter
def to_jalali(value):
    if not value:
        return ''
    if isinstance(value, str):
        return value
    months = 'فروردین اردیبهشت خرداد تیر مرداد شهریور مهر آبان آذر دی بهمن اسفند'.split()
    try:
        j = jdatetime.datetime.fromgregorian(datetime=value)
        return f'{j.day} {months[j.month - 1]} {j.year}'
    except (TypeError, AttributeError):
        pass
    try:
        j = jdatetime.date.fromgregorian(date=value)
        return f'{j.day} {months[j.month - 1]} {j.year}'
    except (TypeError, AttributeError):
        pass
    return str(value)


@register.filter
def persian_numbers(value):
    persian_digits = '۰۱۲۳۴۵۶۷۸۹'
    try:
        return str(value).translate(str.maketrans('0123456789', persian_digits))
    except (TypeError, ValueError):
        return str(value)


@register.filter
def price_fa(value):
    try:
        persian_digits = '۰۱۲۳۴۵۶۷۸۹'
        formatted = f'{int(value):,}'
        persian = formatted.translate(str.maketrans('0123456789', persian_digits))
        return f'{persian} تومان'
    except (ValueError, TypeError):
        return '۰ تومان'


@register.simple_tag
def site_setting(key, default=''):
    from main.models import Setting
    try:
        s = Setting.objects.get(key=key)
        return s.value or default
    except Setting.DoesNotExist:
        return default
