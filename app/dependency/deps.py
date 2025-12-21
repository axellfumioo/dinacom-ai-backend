from fastapi import Header, HTTPException, status
from app.core.config import settings

def verify_token(authorization: str = Header(...)):
    """
    Expect:
    Authorization: Bearer <TOKEN>
    """

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization format"
        )

    token = authorization.replace("Bearer ", "")

    if token != settings.secret_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )

    return True
