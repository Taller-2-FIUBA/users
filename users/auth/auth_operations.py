"""All authentication related operations."""
import jwt

# This should be an actual key, and it shouldn't be stored here
SECRET_KEY = "secret"


def decode_token(encoded_jwt):
    """Decode JWT."""
    return jwt.decode(encoded_jwt, SECRET_KEY, algorithms=["HS256"])


def encode_token(role: str, _id: str):
    """Return JWT with specified role and id."""
    data = {"role": role, "id": _id}
    return jwt.encode(data, SECRET_KEY, algorithm="HS256")
