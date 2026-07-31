from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session

from backend.core.auth import hash_password
from backend.core.auth import verify_password
from backend.core.auth import create_access_token
from backend.database.session import SessionLocal
from backend.models.user import User
from backend.schemas.auth import RegisterRequest
from backend.schemas.auth import LoginRequest
from backend.schemas.auth import TokenResponse


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


def get_db():
    db = SessionLocal()

    try:
        yield db
    finally:
        db.close()


@router.post("/register")
def register(
    data: RegisterRequest,
    db: Session = Depends(get_db)
):
    existing_user = db.query(User).filter(
        User.username == data.username
    ).first()

    if existing_user:
        return {
            "error": "Username already exists"
        }

    user = User(
    username=data.username,
    email=data.email,
    hashed_password=hash_password(data.password),
    role="USER"
)

    db.add(user)
    db.commit()
    db.refresh(user)

    return {
        "message": "User registered successfully",
        "username": user.username
    }


@router.post(
    "/login",
    response_model=TokenResponse
)
def login(
    data: LoginRequest,
    db: Session = Depends(get_db)
):
    user = db.query(User).filter(
        User.username == data.username
    ).first()

    if not user or not verify_password(
        data.password,
        user.hashed_password
    ):
        return {
            "access_token": "",
            "token_type": "invalid"
        }

    token = create_access_token({
    "sub": str(user.id),
    "username": user.username,
    "role": user.role
})

    return {
        "access_token": token,
        "token_type": "bearer"
    }