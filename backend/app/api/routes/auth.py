from fastapi import APIRouter, HTTPException, Depends, status
from app.schemas.user import LoginRequest, LoginResponse
from app.core.security import create_access_token, get_current_user
from app.db.database import get_db_connection, verify_password

router = APIRouter()


@router.post("/login", response_model=LoginResponse)
def login(req: LoginRequest):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT username, password_hash, role FROM users WHERE username = ?", (req.username,))
        user = cursor.fetchone()

    if not user or not verify_password(req.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password"
        )

    # Issue real signed JWT token
    token = create_access_token(data={"sub": user["username"], "role": user["role"]})
    return LoginResponse(
        access_token=token,
        role=user["role"],
        note="Signed JWT token issued with role permissions."
    )


@router.get("/me")
def get_current_profile(current_user: dict = Depends(get_current_user)):
    return {
        "username": current_user["username"],
        "role": current_user["role"],
        "authenticated": True
    }
