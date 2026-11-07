import pytest

from ml.url_features import (
    FEATURE_NAMES, URLValidationError, extract_url_features, explain_url,
    levenshtein, registered_domain, shannon_entropy, validate_url,
)


def f(url):
    return extract_url_features(url)


def test_at_least_20_features_fixed_order():
    feats = f("https://www.example.com/about")
    assert len(feats) >= 20
    assert tuple(feats.keys()) == FEATURE_NAMES


def test_same_keys_for_invalid_input():
    assert tuple(f("").keys()) == FEATURE_NAMES
    assert tuple(f(None).keys()) == FEATURE_NAMES


def test_https_flag():
    assert f("https://example.com")["is_https"] == 1
    assert f("http://example.com")["is_https"] == 0


def test_ip_instead_of_domain():
    assert f("http://192.0.2.15/account-update")["has_ip"] == 1
    assert f("http://example.com")["has_ip"] == 0


def test_nonstandard_port():
    assert f("http://example.com:8080/x")["nonstandard_port"] == 1
    assert f("https://example.com:443/x")["nonstandard_port"] == 0


def test_at_symbol_and_double_slash():
    feats = f("http://user@example.com//a//b")
    assert feats["has_at"] == 1
    assert feats["double_slash_in_path"] == 1


def test_shortener():
    assert f("http://bit.ly/prize-claimtest")["is_shortener"] == 1
    assert f("http://example.com/x")["is_shortener"] == 0


def test_suspicious_words_counted():
    assert f("https://login-account.example.com/update")["num_suspicious_words"] >= 3


def test_punycode_detected():
    assert f("http://xn--exmplecua.test/secure/login?verify=1")["has_punycode"] == 1


def test_subdomains_and_dots():
    feats = f("http://a.b.c.example.com/")
    assert feats["num_subdomains"] == 3
    assert feats["num_dots"] == 4


def test_query_params_and_special_chars():
    feats = f("http://example.com/p?a=1&b=2&c=3")
    assert feats["num_query_params"] == 3
    assert feats["num_special_chars"] >= 6


def test_suspicious_tld():
    assert f("http://prize.example.xyz")["suspicious_tld"] == 1
    assert f("http://example.org")["suspicious_tld"] == 0


def test_brand_similarity():
    assert f("http://kasp1.kz")["brand_similarity"] == 1
    assert f("http://kaspi.kz")["brand_similarity"] == 0  # нақты бренд


def test_entropy_ordering():
    assert shannon_entropy("aaaa") == 0
    assert shannon_entropy("abcd") > shannon_entropy("aabb")


def test_levenshtein():
    assert levenshtein("kaspi", "kasp1") == 1
    assert levenshtein("abc", "abc") == 0


def test_scheme_less_url_accepted():
    assert validate_url("example.com/page").startswith("http://")


@pytest.mark.parametrize("bad", ["", "   ", "http://", "ftp://example.com",
                                 "http://exa mple.com", "http://localhost", "a" * 2100])
def test_validate_rejects_bad_input(bad):
    with pytest.raises(URLValidationError):
        validate_url(bad)


@pytest.mark.parametrize("bad", ["", None, 123, b"bytes", "http://", "\x00\x01"])
def test_extract_never_raises(bad):
    assert tuple(extract_url_features(bad).keys()) == FEATURE_NAMES


def test_explain_url_reasons_in_russian():
    reasons = explain_url(f("http://192.0.2.15:8080/account-update"))
    assert any("IP-адрес" in r for r in reasons)
    assert any("порт" in r for r in reasons)


def test_registered_domain():
    assert registered_domain("http://a.b.example.com/x") == "example.com"
