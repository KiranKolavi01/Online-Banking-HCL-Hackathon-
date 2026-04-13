import bcrypt

def hash_password(password: str) -> str:
    # Hashes password with bcrypt
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def check_password(password: str, hashed: str) -> bool:
    # Verifies credentials
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))
