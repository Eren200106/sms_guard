"""9-тапсырма: URL-дан құрылымдық белгілерді шығару.

ЕСКЕРТУ: бұл модульде желілік сұраулар ЖОҚ (requests, socket, DNS қолданылмайды).
URL тек жол ретінде талданады. Тесттерде тек example.com / example.org / .test домендері.
"""
from __future__ import annotations

import ipaddress
import math
import re
from collections import Counter
from urllib.parse import parse_qsl, urlparse

MAX_URL_LENGTH = 2048

# ---- tldextract (болмаса, қарапайым резервтік әдіс) ----
try:  # pragma: no cover - орта тәуелді
    import tldextract

    # suffix_list_urls=() -> интернетке шықпайды, кітапхана ішіндегі тізімді қолданады
    _TLD = tldextract.TLDExtract(suffix_list_urls=())
except Exception:  # pragma: no cover
    _TLD = None

URL_SHORTENERS = frozenset(
    """
    bit.ly tinyurl.com goo.gl t.co is.gd cutt.ly ow.ly clck.ru buff.ly rebrand.ly
    shorturl.at tiny.cc rb.gy v.gd t.ly lnkd.in s.id vk.cc u.to qps.ru
    """.split()
)

SUSPICIOUS_WORDS = (
    "login", "verify", "secure", "account", "update", "bank", "confirm",
    "password", "bonus", "free", "prize", "kaspi", "halyk", "signin", "wallet",
    "gift", "claim", "unlock", "suspend", "billing",
)

SUSPICIOUS_TLDS = frozenset(
    "xyz top click zip loan work gq tk ml cf ga icu monster country support".split()
)  # Дереккөзі: Spamhaus "Most abused TLDs" / Interisle есептері. Есепте дәлелдеңіз.

BRAND_DOMAINS = (
    "kaspi.kz", "halykbank.kz", "jusan.kz", "forte.kz", "freedombank.kz",
    "sberbank.ru", "tinkoff.ru", "vtb.ru", "alfabank.ru", "gosuslugi.ru",
    "egov.kz", "kazpost.kz", "paypal.com", "google.com", "apple.com",
    "microsoft.com", "amazon.com", "facebook.com", "instagram.com",
    "whatsapp.com", "netflix.com", "dhl.com", "fedex.com", "binance.com",
)

SPECIAL_CHARS = "@~%=&_?"

FEATURE_NAMES = (
    "url_length", "host_length", "path_length", "num_dots", "num_subdomains",
    "num_hyphens_domain", "num_digits", "digit_ratio_domain", "num_special_chars",
    "has_ip", "is_https", "nonstandard_port", "has_at", "double_slash_in_path",
    "is_shortener", "num_suspicious_words", "has_punycode", "mixed_scripts",
    "brand_similarity", "domain_entropy", "suspicious_tld", "num_query_params",
)

_CTRL_RE = re.compile(r"[\x00-\x1f\x7f\s]")


class URLValidationError(ValueError):
    """Пайдаланушыға көрсетуге болатын түсінікті қате."""


# --------------------------------------------------------------------- валидация
def validate_url(url) -> str:
    """URL форматын тексереді және талдауға арналған (схемасы бар) жолды қайтарады.

    Схемасыз URL-ға талдау үшін http:// қосылады. Қате болса URLValidationError.
    """
    if not isinstance(url, str):
        raise URLValidationError("Ссылка должна быть строкой")
    url = url.strip()
    if not url:
        raise URLValidationError("Ссылка не может быть пустой")
    if len(url) > MAX_URL_LENGTH:
        raise URLValidationError(f"Ссылка длиннее {MAX_URL_LENGTH} символов")
    if _CTRL_RE.search(url):
        raise URLValidationError("Ссылка содержит пробелы или управляющие символы")

    if "://" in url:
        scheme = url.split("://", 1)[0].lower()
        if scheme not in ("http", "https"):
            raise URLValidationError("Допустимы только схемы http и https")
        normalized = url
    else:
        normalized = "http://" + url

    try:
        parsed = urlparse(normalized)
        _ = parsed.port  # некорректный порт -> ValueError
    except ValueError:
        raise URLValidationError("Некорректный адрес или порт") from None

    host = parsed.hostname
    if not host:
        raise URLValidationError("В ссылке не найден домен")
    if not _is_ip(host) and "." not in host:
        raise URLValidationError("Домен должен содержать точку (например, example.com)")
    return normalized


# --------------------------------------------------------------------- помощники
def _is_ip(host: str) -> bool:
    try:
        ipaddress.ip_address(host.strip("[]"))
        return True
    except ValueError:
        return False


def _split_host(host: str) -> tuple[str, str, str]:
    """(subdomain, domain, suffix). IP үшін бос жолдар."""
    if _is_ip(host):
        return "", "", ""
    if _TLD is not None:
        ext = _TLD(host)
        return ext.subdomain, ext.domain, ext.suffix
    labels = host.split(".")
    if len(labels) < 2:
        return "", host, ""
    return ".".join(labels[:-2]), labels[-2], labels[-1]


def registered_domain(url: str) -> str:
    """Тіркелген домен (GroupShuffleSplit топтары үшін). Қате болса бос жол."""
    try:
        host = urlparse(validate_url(url)).hostname or ""
    except URLValidationError:
        return ""
    sub, dom, suf = _split_host(host)
    if not dom:
        return host
    return f"{dom}.{suf}" if suf else dom


def shannon_entropy(text: str) -> float:
    if not text:
        return 0.0
    n = len(text)
    return -sum((c / n) * math.log2(c / n) for c in Counter(text).values())


def levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]


def _has_mixed_scripts(host: str) -> bool:
    labels = []
    for label in host.split("."):
        if label.startswith("xn--"):
            try:
                label = label.encode("ascii").decode("idna")
            except Exception:
                pass
        labels.append(label)
    text = "".join(labels)
    has_cyr = any("\u0400" <= ch <= "\u04ff" for ch in text)
    has_lat = any("a" <= ch.lower() <= "z" for ch in text)
    return has_cyr and has_lat


def _brand_lookalike(domain: str, suffix: str) -> bool:
    """Домен бренд атына ұқсас (Левенштейн <= 2), бірақ нақты бренд домені емес."""
    if not domain:
        return False
    registered = f"{domain}.{suffix}" if suffix else domain
    for brand in BRAND_DOMAINS:
        if registered == brand:
            return False  # бренд өзі
    for brand in BRAND_DOMAINS:
        name = brand.split(".")[0]
        if len(name) < 4:
            continue
        # домен ішінде "kaspi-bank" сияқты бренд атауы кездесуі де ескеріледі
        parts = [domain] + domain.split("-")
        if any(levenshtein(p, name) <= 2 for p in parts if len(p) >= 4):
            return True
    return False


def _zero_features() -> dict:
    return {name: 0 for name in FEATURE_NAMES}


# --------------------------------------------------------------------- негізгі функция
def extract_url_features(url) -> dict:
    """URL-дан 22 белгі шығарады. Кілттер реті тұрақты (FEATURE_NAMES).

    Қате енгізу кезінде өңделмеген ерекше жағдай шықпайды: нөлдік белгілер қайтады.
    Алдымен validate_url арқылы қатені пайдаланушыға түсіндіріңіз.
    """
    try:
        normalized = validate_url(url)
    except URLValidationError:
        return _zero_features()

    original = url.strip()
    parsed = urlparse(normalized)
    host = (parsed.hostname or "").lower()
    path = parsed.path or ""
    sub, dom, suf = _split_host(host)
    has_ip = _is_ip(host)
    lowered = normalized.lower()

    digits_in_host = sum(ch.isdigit() for ch in host)
    port = parsed.port
    query_params = parse_qsl(parsed.query, keep_blank_values=True)
    sub_labels = [x for x in sub.split(".") if x] if sub else []

    feats = {
        "url_length": len(original),
        "host_length": len(host),
        "path_length": len(path),
        "num_dots": original.count("."),
        "num_subdomains": len(sub_labels),
        "num_hyphens_domain": host.count("-"),
        "num_digits": sum(ch.isdigit() for ch in original),
        "digit_ratio_domain": round(digits_in_host / len(host), 4) if host else 0.0,
        "num_special_chars": sum(original.count(ch) for ch in SPECIAL_CHARS),
        "has_ip": int(has_ip),
        "is_https": int(parsed.scheme.lower() == "https"),
        "nonstandard_port": int(port is not None and port not in (80, 443)),
        "has_at": int("@" in original),
        "double_slash_in_path": int("//" in path),
        "is_shortener": int(host.removeprefix("www.") in URL_SHORTENERS),
        "num_suspicious_words": sum(w in lowered.split("://", 1)[-1] for w in SUSPICIOUS_WORDS),
        "has_punycode": int(any(l.startswith("xn--") for l in host.split("."))),
        "mixed_scripts": int(_has_mixed_scripts(host)),
        "brand_similarity": int(_brand_lookalike(dom, suf)) if not has_ip else 0,
        "domain_entropy": round(shannon_entropy(host), 4),
        "suspicious_tld": int(suf.split(".")[-1] in SUSPICIOUS_TLDS) if suf else 0,
        "num_query_params": len(query_params),
    }
    # Кілттер реті тұрақты болуы үшін FEATURE_NAMES бойынша жинаймыз
    return {name: feats[name] for name in FEATURE_NAMES}


# --------------------------------------------------------------------- түсіндіру
def explain_url(features: dict) -> list[str]:
    """Белгілер бойынша адамға түсінікті себептер тізімі (орыс тілінде)."""
    reasons: list[str] = []
    f = features
    if f.get("has_ip"):
        reasons.append("Используется IP-адрес вместо доменного имени")
    if f.get("has_punycode"):
        reasons.append("Домен содержит Punycode (xn--) — возможна маскировка под другой сайт")
    if f.get("mixed_scripts"):
        reasons.append("В домене смешаны кириллица и латиница")
    if f.get("brand_similarity"):
        reasons.append("Домен похож на название известного бренда, но не совпадает с ним")
    if f.get("is_shortener"):
        reasons.append("Используется сервис сокращения ссылок — настоящий адрес скрыт")
    if f.get("has_at"):
        reasons.append("В адресе есть символ @ — часть адреса может быть подменена")
    if f.get("nonstandard_port"):
        reasons.append("Указан нестандартный порт")
    if f.get("double_slash_in_path"):
        reasons.append("В пути ссылки встречается двойной слэш //")
    if f.get("suspicious_tld"):
        reasons.append("Доменная зона часто используется в мошеннических рассылках")
    n = f.get("num_suspicious_words", 0)
    if n:
        reasons.append(f"В ссылке найдено подозрительных слов: {n} (login, verify, secure и т. п.)")
    if f.get("num_subdomains", 0) >= 3:
        reasons.append("Слишком много поддоменов")
    if f.get("num_hyphens_domain", 0) >= 3:
        reasons.append("В домене много дефисов")
    if f.get("url_length", 0) > 100:
        reasons.append("Очень длинная ссылка")
    if not f.get("is_https") and f.get("url_length", 0):
        reasons.append("Соединение без шифрования (нет HTTPS)")
    return reasons
