import bcrypt, base64, hashlib

def encrypt_plain_password(password: str) -> bytes:
    password_bytes = password.encode('utf-8')
    password_b64 = base64.b64encode(hashlib.sha256(password_bytes).digest())
    return bcrypt.hashpw(password_b64, bcrypt.gensalt())

def check_password(encrypted_pswd: bytes, password: str) -> bool:
    password_bytes = password.encode('utf-8')
    password_b64 = base64.b64encode(hashlib.sha256(password_bytes).digest())
    return bcrypt.checkpw(password_b64, encrypted_pswd)