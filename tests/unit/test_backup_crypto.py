import base64, io, os
import pytest
from cryptography.exceptions import InvalidTag
from app.core.security import SecretBox

# scripts is on repository path during tests.
from scripts.backup_crypto import encrypt_stream,decrypt_stream


def key(): return os.urandom(32)

def test_backup_crypto_roundtrip_multi_chunk():
    plain=os.urandom(2_300_000); encrypted=io.BytesIO()
    encrypt_stream(io.BytesIO(plain),encrypted,key_bytes:=key())
    restored=io.BytesIO(); decrypt_stream(io.BytesIO(encrypted.getvalue()),restored,key_bytes)
    assert restored.getvalue()==plain and encrypted.getvalue()!=plain

def test_backup_crypto_detects_tampering():
    encrypted=io.BytesIO(); key_bytes=key(); encrypt_stream(io.BytesIO(b'financial-evidence'),encrypted,key_bytes)
    data=bytearray(encrypted.getvalue()); data[-6]^=1
    with pytest.raises(InvalidTag): decrypt_stream(io.BytesIO(data),io.BytesIO(),key_bytes)
