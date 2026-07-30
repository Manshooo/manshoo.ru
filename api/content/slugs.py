from django.utils.text import slugify

# Кириллица в slug технически допустима, но в ссылке превращается в
# процентную кашу — поэтому названия транслитерируем.
TRANSLIT = {
    "а": "a",
    "б": "b",
    "в": "v",
    "г": "g",
    "д": "d",
    "е": "e",
    "ё": "e",
    "ж": "zh",
    "з": "z",
    "и": "i",
    "й": "y",
    "к": "k",
    "л": "l",
    "м": "m",
    "н": "n",
    "о": "o",
    "п": "p",
    "р": "r",
    "с": "s",
    "т": "t",
    "у": "u",
    "ф": "f",
    "х": "h",
    "ц": "c",
    "ч": "ch",
    "ш": "sh",
    "щ": "sch",
    "ъ": "",
    "ы": "y",
    "ь": "",
    "э": "e",
    "ю": "yu",
    "я": "ya",
}


def transliterate(text: str) -> str:
    return "".join(TRANSLIT.get(char, TRANSLIT.get(char.lower(), char)) for char in text)


def make_slug(source: str) -> str:
    """Латинский slug из произвольного названия ('Мой проект' → 'moy-proekt')."""
    return slugify(transliterate(source))
