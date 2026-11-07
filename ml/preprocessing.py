"""4-тапсырма: SMS мәтінін тазалау және нормализациялау.

Бір ғана normalize_sms функциясы ноутбукте де, веб-қосымшада да қолданылады.
Функция таза (side effect жоқ).
"""
from __future__ import annotations

import re
import unicodedata

# Токендер (ТЗ 4-тапсырма, 3-тармақ)
URL_TOKEN = "<url>"
EMAIL_TOKEN = "<email>"
PHONE_TOKEN = "<phone>"
MONEY_TOKEN = "<money>"
NUM_TOKEN = "<num>"

_URL_SCHEME_RE = re.compile(r"(?:https?://|www\.)\S*[^\s.,;:!?)\]\"'»]")
_URL_BARE_RE = re.compile(
    r"\b(?:[a-z0-9а-яёәғқңөұүһі-]+\.)+"
    r"(?:com|net|org|info|ru|kz|xyz|top|click|zip|ly|io|me|co|gl|is|example|test)"
    r"(?:/\S*[^\s.,;:!?)\]\"'»])?\b"
)
_EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")

_CURRENCY = r"(?:[$£€₸₽]|руб\w*|тг\b|тенге|теңге|usd|eur|kzt|долл\w*)"
_AMOUNT = r"\d(?:[\d\s.,]*\d)?"
_MONEY_RE = re.compile(
    rf"{_CURRENCY}\s?{_AMOUNT}|{_AMOUNT}\s?{_CURRENCY}"
)
_PHONE_RE = re.compile(r"(?<![\w<])\+?\d[\d\s\-()]{7,}\d")
_NUM_RE = re.compile(r"\b\d{1,3}(?:[ \u00a0]\d{3})+(?:[.,]\d+)?\b|\b\d+(?:[.,]\d+)?\b")
_REPEAT_PUNCT_RE = re.compile(r"([!?])\1+")
_SPACES_RE = re.compile(r"\s+")

# Қосымша (опция): шағын стоп-сөз жиыны. NLTK жүктеуді қажет етпеу үшін ішіне салынған.
STOPWORDS = frozenset(
    """
    и в во не что он на я с со как а то все она так его но да ты к у же вы за бы по
    только ее мне было вот от меня еще нет о из ему теперь когда даже ну вдруг ли
    если уже или ни быть был него до вас нибудь опять уж вам ведь там потом себя
    ничего ей может они тут где есть надо ней для мы тебя их чем была сам чтоб без
    будто чего раз тоже себе под будет ж тогда кто этот того потому этого какой
    the a an and or of to in on at for is are was were be been it this that with
    as by from i you he she we they my your our their me him her us them
    және мен сен ол біз сіз олар бұл сол да де та те үшін бір
    """.split()
)


def normalize_sms(text, remove_stopwords: bool = False) -> str:
    """SMS мәтінін нормализациялайды.

    Қадамдар: NFKC -> төменгі регистр -> басқару символдарын жою ->
    URL/email/сома/телефон/сан токендері -> қайталанатын !/? қысқарту ->
    артық бос орындарды жою -> (опция) стоп-сөздерді жою.
    Қазақ әріптері (ә ғ қ ң ө ұ ү һ і) сақталады.
    """
    if text is None or not isinstance(text, str):
        return ""

    s = unicodedata.normalize("NFKC", text).lower()
    # Басқару символдары (категория C*) жойылады; жол үзілімі/табуляция бос орынға айналады.
    s = "".join(
        " " if ch in "\n\r\t" else ch
        for ch in s
        if ch in "\n\r\t" or unicodedata.category(ch)[0] != "C"
    )

    s = _URL_SCHEME_RE.sub(URL_TOKEN, s)   # http://..., www....
    s = _EMAIL_RE.sub(EMAIL_TOKEN, s)      # email URL-дан бұрын (help@example.com)
    s = _URL_BARE_RE.sub(URL_TOKEN, s)     # схемасыз: bit.ly/abc
    s = _MONEY_RE.sub(MONEY_TOKEN, s)
    s = _PHONE_RE.sub(PHONE_TOKEN, s)
    s = _NUM_RE.sub(NUM_TOKEN, s)

    # "!!!" -> "!" : леп сақталады (қысым белгісі), қайталануы жойылады
    s = _REPEAT_PUNCT_RE.sub(r"\1", s)
    s = _SPACES_RE.sub(" ", s).strip()

    if remove_stopwords:
        s = " ".join(w for w in s.split(" ") if w not in STOPWORDS)
    return s
