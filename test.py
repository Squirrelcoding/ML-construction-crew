from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

hashed = pwd_context.hash("password123")
print(f"HASHED: {hashed}")  # prints the bcrypt hashed version

# Later, to verify
is_correct = pwd_context.verify("password123", hashed)
print(is_correct)  # True if password matches
