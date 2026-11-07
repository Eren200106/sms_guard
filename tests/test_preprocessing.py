from ml.preprocessing import normalize_sms


def test_empty_and_none():
    assert normalize_sms("") == ""
    assert normalize_sms(None) == ""
    assert normalize_sms("   \n\t ") == ""


def test_only_url():
    assert normalize_sms("http://secure-bank-verify.example/login") == "<url>"
    assert normalize_sms("www.example.com") == "<url>"


def test_mixed_case_lowercased():
    assert normalize_sms("ВАША Карта ЗАБЛОКИРОВАНА") == "ваша карта заблокирована"


def test_cyrillic_preserved():
    out = normalize_sms("Привет! Встречаемся завтра")
    assert "привет" in out and "встречаемся" in out


def test_kazakh_letters_preserved():
    text = "Әріптер: ә ғ қ ң ө ұ ү һ і"
    out = normalize_sms(text)
    for ch in "әғқңөұүһі":
        assert ch in out


def test_money_tokens():
    assert "<money>" in normalize_sms("Вам начислено $1000")
    assert "<money>" in normalize_sms("Оплатите сбор 350 ₸")
    assert "<money>" in normalize_sms("Переведите 5000 руб сегодня")


def test_phone_tokens():
    out = normalize_sms("Звоните +7 701 123 45 67 срочно")
    assert "<phone>" in out
    assert "701" not in out


def test_numbers_and_email():
    out = normalize_sms("Заказ 4821 отправлен, пишите на help@example.com")
    assert "<num>" in out and "<email>" in out


def test_emoji_and_control_chars():
    out = normalize_sms("Ура!!! 🎉\x00\x07 выигрыш")
    assert "🎉" in out
    assert "\x00" not in out and "\x07" not in out
    assert "!!!" not in out and "!" in out


def test_spaces_collapsed():
    assert normalize_sms("a    b \n\n c") == "a b c"


def test_pure_function_does_not_mutate():
    original = "Срочно!!!  http://x.example"
    normalize_sms(original)
    assert original == "Срочно!!!  http://x.example"


def test_stopwords_option():
    assert "the" not in normalize_sms("the prize is here", remove_stopwords=True).split()
