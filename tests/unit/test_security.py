import pytest,time
from app.core.security import hash_password,verify_password,SecretBox,ConfirmationStore,fingerprint

def test_argon_roundtrip():
    h=hash_password('a-very-long-password'); assert verify_password(h,'a-very-long-password'); assert not verify_password(h,'wrong')
def test_short_password_rejected():
    with pytest.raises(ValueError): hash_password('short')
def test_secret_box():
    key=SecretBox.generate_key(); box=SecretBox(key); enc=box.encrypt('SECRET'); assert enc!='SECRET'; assert box.decrypt(enc)=='SECRET'
def test_fingerprint_not_secret(): assert fingerprint('abc')!='abc'
def test_confirmation_single_use():
    s=ConfirmationStore(); n=s.issue('LIVE',60); assert s.consume(n,'LIVE'); assert not s.consume(n,'LIVE')
def test_confirmation_wrong_action():
    s=ConfirmationStore(); n=s.issue('LIVE',60); assert not s.consume(n,'PANIC')
def test_confirmation_expiry():
    s=ConfirmationStore(); n=s.issue('LIVE',0); time.sleep(.001); assert not s.consume(n,'LIVE')
