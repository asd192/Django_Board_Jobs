from typing import Union

from django import template

register = template.Library()


@register.filter()
def ru_pluralize(number: Union[int, str], arg: str = 'текст, тексты, текстов'):
    nominative_singular, nominative_plural, genitive_plural = arg.split(', ')

    number = abs(int(number))

    if (number % 10) == 1 and number % 100 != 11:
        return f'{number} {nominative_singular}'
    elif 2 <= number % 10 <= 4 and number // 10 % 10 != 1:
        return f'{number} {nominative_plural}'
    else:
        return f'{number} {genitive_plural}'


@register.filter()
def list_li(tags_str):
    tags_str = tags_str.split(',')
    tags = '</li><li>'.join(tags_str)

    return f'<li>{tags}</li>'
