from pydantic import BaseModel
from typing import Literal

Role = Literal["public", "staff", "control_room", "admin"]


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    """TODO(Antigravity): replace with a real signed JWT + expiry.
    This just returns the static demo token from config so the admin
    routes are exercisable end-to-end before real auth exists."""
    access_token: str
    role: Role
    note: str = "Demo token only — see app/core/security.py TODO."
