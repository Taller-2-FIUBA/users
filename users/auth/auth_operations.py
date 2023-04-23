"""All authentication related operations."""
import jwt
from fastapi import Request

# This should be an actual key, and it shouldn't be stored here
SECRET_KEY = "secret"


def decode_token(encoded_jwt):
    """Decode JWT."""
    return jwt.decode(encoded_jwt, SECRET_KEY, algorithms=["HS256"])


def encode_token(role: str, _id: str):
    """Return JWT with specified role and id."""
    data = {"role": role, "id": _id}
    return jwt.encode(data, SECRET_KEY, algorithm="HS256")


def get_token(request: Request):
    """Get token from request."""
    token = request.headers.get("Authorization").split(' ')[1]
    return decode_token(token)
