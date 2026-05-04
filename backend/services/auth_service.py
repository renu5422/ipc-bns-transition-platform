import hashlib
import os

class AuthService:
    def verify_password(self, plain: str, hashed: str) -> bool:
        # Use a proper password hashing library (e.g., bcrypt) in production
        salt, stored_hash = hashed.split(":", 1)
        return stored_hash == hashlib.sha256((salt + plain).encode()).hexdigest()

    def hash_password(self, plain: str) -> str:
        salt = os.urandom(16).hex()
        hashed = hashlib.sha256((salt + plain).encode()).hexdigest()
        return f"{salt}:{hashed}"

auth_service = AuthService()
