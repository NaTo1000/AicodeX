"""
Tests for AicodeX codec registry and rollover fallback chains
"""

import base64
import os
import sys
import zlib

import pytest

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from aicodex_codecs import CodecRegistry, CodecError


def test_builtin_codecs_registered():
    """All built-in codecs are registered"""
    registry = CodecRegistry()
    available = registry.available()
    for name in ("utf-8", "base64", "hex", "zlib", "rot13"):
        assert name in available


def test_roundtrip_each_codec():
    """Each codec round-trips a payload"""
    registry = CodecRegistry()
    payload = b'{"window": {"width": 400}}'
    for name in ("utf-8", "base64", "hex", "zlib", "rot13"):
        encoded = registry.encode(payload, [name])
        assert registry.decode(encoded, [name]) == payload


def test_encode_uses_primary_codec():
    """Encoding uses the first codec of the chain"""
    registry = CodecRegistry()
    payload = b"hello"
    encoded = registry.encode(payload, ["base64", "utf-8"])
    assert encoded == base64.b64encode(payload)


def test_encode_accepts_str():
    """Encoding accepts str input (converted to utf-8 bytes)"""
    registry = CodecRegistry()
    encoded = registry.encode("hello", ["utf-8"])
    assert encoded == b"hello"


def test_decode_rollover_fallback():
    """Decoding rolls over the chain until one codec succeeds"""
    registry = CodecRegistry()
    payload = b"hello world"
    # Payload encoded with zlib; chain starts with codecs that must fail.
    encoded = zlib.compress(payload)
    assert registry.decode(encoded, ["base64", "hex", "zlib"]) == payload


def test_decode_rollover_plain_text():
    """Plain text payload falls through binary codecs to utf-8"""
    registry = CodecRegistry()
    payload = "plain text ✓"
    encoded = payload.encode("utf-8")
    assert registry.decode(encoded, ["zlib", "base64", "utf-8"]) == encoded


def test_decode_all_codecs_fail():
    """CodecError raised when every codec in the chain fails"""
    registry = CodecRegistry()
    with pytest.raises(CodecError):
        registry.decode(b"\x00\xff\xfebinary garbage", ["zlib", "base64", "hex"])


def test_unknown_codec_raises():
    """Unknown codec names raise CodecError"""
    registry = CodecRegistry()
    with pytest.raises(CodecError):
        registry.get("no-such-codec")
    with pytest.raises(CodecError):
        registry.encode(b"x", ["no-such-codec"])


def test_empty_chain_defaults_to_utf8():
    """An empty chain falls back to utf-8"""
    registry = CodecRegistry()
    payload = b"data"
    assert registry.decode(registry.encode(payload, []), []) == payload


def test_register_custom_codec():
    """Custom codecs can be registered and used"""
    from aicodex_codecs import BaseCodec

    class ReverseCodec(BaseCodec):
        name = "reverse"

        def encode(self, payload):
            return bytes(payload)[::-1]

        def decode(self, payload):
            return bytes(payload)[::-1]

    registry = CodecRegistry()
    registry.register(ReverseCodec())
    payload = b"abcdef"
    assert registry.decode(registry.encode(payload, ["reverse"]), ["reverse"]) == payload
