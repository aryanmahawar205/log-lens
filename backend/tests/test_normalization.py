import pytest
from app.normalization.url import URLNormalizer

def test_url_normalizer_numeric():
    assert URLNormalizer.normalize("/user/123/profile") == "/user/{id}/profile"
    assert URLNormalizer.normalize("/product/100") == "/product/{id}"
    assert URLNormalizer.normalize("/home") == "/home"

def test_url_normalizer_uuid():
    assert URLNormalizer.normalize("/doc/123e4567-e89b-12d3-a456-426614174000/edit") == "/doc/{id}/edit"

def test_url_normalizer_hash():
    assert URLNormalizer.normalize("/token/abcdef1234567890/validate") == "/token/{id}/validate"
