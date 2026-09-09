"""
Codec registry for AicodeX
Provides pluggable codecs for encoding/decoding configuration section
payloads with a full rollover fallback chain: decoding tries each codec
in the chain, in order, until one succeeds.
"""

import base64
import codecs as _stdlib_codecs
import zlib


class CodecError(Exception):
    """Raised when a codec fails to encode or decode a payload."""


class BaseCodec:
    """Base class for codecs."""

    name = "base"

    def encode(self, payload: bytes) -> bytes:
        """Encode raw bytes, returning encoded bytes."""
        raise NotImplementedError

    def decode(self, payload: bytes) -> bytes:
        """Decode encoded bytes, returning raw bytes."""
        raise NotImplementedError

    def matches(self, payload: bytes) -> bool:
        """Return True if the payload looks like it was encoded by this codec."""
        try:
            self.decode(payload)
            return True
        except CodecError:
            return False


class Utf8Codec(BaseCodec):
    """Pass-through codec for plain UTF-8 text payloads."""

    name = "utf-8"

    def encode(self, payload: bytes) -> bytes:
        if not isinstance(payload, (bytes, bytearray)):
            raise CodecError("utf-8 codec expects bytes input")
        try:
            bytes(payload).decode("utf-8")
        except (UnicodeDecodeError, ValueError) as e:
            raise CodecError(f"payload is not valid utf-8: {e}") from e
        return bytes(payload)

    def decode(self, payload: bytes) -> bytes:
        try:
            bytes(payload).decode("utf-8")
        except (UnicodeDecodeError, ValueError) as e:
            raise CodecError(f"payload is not valid utf-8: {e}") from e
        return bytes(payload)


class Base64Codec(BaseCodec):
    """Base64 codec."""

    name = "base64"

    def encode(self, payload: bytes) -> bytes:
        return base64.b64encode(bytes(payload))

    def decode(self, payload: bytes) -> bytes:
        try:
            return base64.b64decode(bytes(payload), validate=True)
        except Exception as e:
            raise CodecError(f"payload is not valid base64: {e}") from e


class HexCodec(BaseCodec):
    """Hexadecimal codec."""

    name = "hex"

    def encode(self, payload: bytes) -> bytes:
        return bytes(payload).hex().encode("ascii")

    def decode(self, payload: bytes) -> bytes:
        try:
            return bytes.fromhex(bytes(payload).decode("ascii"))
        except (ValueError, UnicodeDecodeError) as e:
            raise CodecError(f"payload is not valid hex: {e}") from e


class ZlibCodec(BaseCodec):
    """Zlib compression codec."""

    name = "zlib"

    def encode(self, payload: bytes) -> bytes:
        return zlib.compress(bytes(payload))

    def decode(self, payload: bytes) -> bytes:
        try:
            return zlib.decompress(bytes(payload))
        except zlib.error as e:
            raise CodecError(f"payload is not valid zlib: {e}") from e


class Rot13Codec(BaseCodec):
    """ROT13 codec (legacy text payloads)."""

    name = "rot13"

    def encode(self, payload: bytes) -> bytes:
        return self.decode(payload)

    def decode(self, payload: bytes) -> bytes:
        try:
            text = bytes(payload).decode("utf-8")
            return _stdlib_codecs.decode(text, "rot_13").encode("utf-8")
        except (UnicodeDecodeError, ValueError) as e:
            raise CodecError(f"payload is not valid rot13 text: {e}") from e


class CodecRegistry:
    """Registry of codecs with per-section rollover fallback chains.

    Each section is assigned an ordered chain of codec names. Encoding
    always uses the primary (first) codec of the chain. Decoding performs
    a full rollover: it tries each codec in the chain, in order, and
    returns the first successful decode. This makes payloads resilient to
    codec changes and corruption: if the primary codec cannot read the
    payload, the fallbacks are attempted automatically.
    """

    def __init__(self):
        """Initialize the registry with the built-in codecs."""
        self._codecs = {}
        for codec in (Utf8Codec, Base64Codec, HexCodec, ZlibCodec, Rot13Codec):
            self.register(codec())

    def register(self, codec: BaseCodec):
        """Register a codec instance by name."""
        self._codecs[codec.name] = codec

    def get(self, name: str) -> BaseCodec:
        """Get a codec by name, raising CodecError if unknown."""
        codec = self._codecs.get(name)
        if codec is None:
            raise CodecError(f"unknown codec: {name}")
        return codec

    def available(self):
        """Return the list of registered codec names."""
        return sorted(self._codecs.keys())

    def encode(self, payload: bytes, chain) -> bytes:
        """Encode with the primary codec of the chain."""
        if isinstance(payload, str):
            payload = payload.encode("utf-8")
        if not chain:
            chain = ["utf-8"]
        return self.get(chain[0]).encode(payload)

    def decode(self, payload: bytes, chain) -> bytes:
        """Decode with a full rollover fallback over the chain.

        Tries each codec in order and returns the first successful decode.
        Raises CodecError only if every codec in the chain fails.
        """
        if not chain:
            chain = ["utf-8"]
        errors = []
        for name in chain:
            try:
                return self.get(name).decode(payload)
            except CodecError as e:
                errors.append(str(e))
        raise CodecError(
            "all codecs in rollover chain failed: " + "; ".join(errors)
        )
