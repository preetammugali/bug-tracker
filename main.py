
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from pydantic import BaseModel, Field, EmailStr
from supabase import create_client
from dotenv import load_dotenv
from pwdlib import PasswordHash

from typing import Optional
from datetime import datetime, timedelta, timezone

import jwt
import os


# =========================================================
# 1. LOAD ENVIRONMENT VARIABLES
# =========================================================

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

JWT_SECRET = os.getenv("JWT_SECRET")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")

ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
)


# =========================================================
# 2. CHECK ENVIRONMENT VARIABLES
# =========================================================

if not SUPABASE_URL:
    raise Exception("SUPABASE_URL is missing")

if not SUPABASE_KEY:
    raise Exception("SUPABASE_KEY is missing")

if not JWT_SECRET:
    raise Exception("JWT_SECRET is missing")


# =========================================================
# 3. SUPABASE CONNECTION
# =========================================================

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)


# =========================================================
# 4. PASSWORD HASHING
# =========================================================

password_hash = PasswordHash.recommended()


def hash_password(password: str):
    return password_hash.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str
):
    return password_hash.verify(
        plain_password,
        hashed_password
    )


# =========================================================
# 5. FASTAPI APP
# =========================================================

app = FastAPI(
    title="Bug Tracker API",
    description="Bug Tracking System with JWT Authentication and Authorization",
    version="1.0.0"
)
app.mount("/static", StaticFiles(directory="frontend"), name="static")

@app.get("/")
def home():
    return FileResponse("frontend/index.html")

# =========================================================
# 6. CORS
# =========================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# 7. FRONTEND
# =========================================================

app.mount(
    "/frontend",
    StaticFiles(directory="frontend"),
    name="frontend"
)


@app.get("/app")
def frontend():
    return FileResponse("frontend/index.html")


# =========================================================
# 8. PYDANTIC MODELS
# =========================================================

class BugCreate(BaseModel):

    title: str = Field(
        ...,
        min_length=3,
        max_length=200
    )

    description: str

    priority: str = "medium"

    status: str = "open"

    assigned_to: Optional[str] = None


class BugUpdate(BaseModel):

    title: Optional[str] = None

    description: Optional[str] = None

    priority: Optional[str] = None

    status: Optional[str] = None

    assigned_to: Optional[str] = None


class RegisterRequest(BaseModel):

    name: str = Field(
        min_length=2,
        max_length=50
    )

    email: EmailStr

    password: str = Field(
        min_length=6,
        max_length=100
    )


class LoginRequest(BaseModel):

    email: EmailStr

    password: str


# =========================================================
# 9. CREATE JWT TOKEN
# =========================================================

def create_access_token(
    user_id,
    email: str,
    role: str
):

    expire = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": str(user_id),
        "email": email,
        "role": role,
        "exp": expire
    }

    token = jwt.encode(
        payload,
        JWT_SECRET,
        algorithm=JWT_ALGORITHM
    )

    return token


# =========================================================
# 10. OAUTH2 / JWT
# =========================================================

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/login"
)


# =========================================================
# 11. GET CURRENT USER
# =========================================================

def get_current_user(
    token: str = Depends(oauth2_scheme)
):

    try:

        # Decode JWT
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM]
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=401,
                detail="Invalid token"
            )

        # Get user from Supabase
        response = (
            supabase
            .table("users")
            .select("id, name, email, role")
            .eq("id", int(user_id))
            .execute()
        )

        if not response.data:

            raise HTTPException(
                status_code=401,
                detail="User not found"
            )

        return response.data[0]

    except jwt.ExpiredSignatureError:

        raise HTTPException(
            status_code=401,
            detail="Token has expired"
        )

    except jwt.InvalidTokenError:

        raise HTTPException(
            status_code=401,
            detail="Invalid token"
        )

    except ValueError:

        raise HTTPException(
            status_code=401,
            detail="Invalid user ID"
        )


# =========================================================
# 12. ROLE AUTHORIZATION
# =========================================================

def require_roles(*allowed_roles):

    def role_checker(
        current_user: dict = Depends(get_current_user)
    ):

        user_role = current_user.get("role")

        if user_role not in allowed_roles:

            raise HTTPException(
                status_code=403,
                detail="You do not have permission to perform this action"
            )

        return current_user

    return role_checker


# =========================================================
# 13. HOME
# =========================================================

@app.get("/")
def home():

    return {
        "message": "Bug Tracker API is running!",
        "docs": "/docs",
        "frontend": "/app"
    }


# =========================================================
# 14. REGISTER
# =========================================================

@app.post("/register", status_code=201)
def register(user: RegisterRequest):

    # Check whether email already exists

    existing_user = (
        supabase
        .table("users")
        .select("id")
        .eq("email", user.email)
        .execute()
    )

    if existing_user.data:

        raise HTTPException(
            status_code=409,
            detail="Email already registered"
        )

    # Hash password

    hashed_password = hash_password(
        user.password
    )

    # New users are testers by default
    # Admin role should be assigned manually
    # from Supabase by an authorized administrator.

    user_data = {
        "name": user.name,
        "email": user.email,
        "password_hash": hashed_password,
        "role": "tester"
    }

    response = (
        supabase
        .table("users")
        .insert(user_data)
        .execute()
    )

    if not response.data:

        raise HTTPException(
            status_code=500,
            detail="Failed to create user"
        )

    created_user = response.data[0]

    return {
        "message": "Registration successful",
        "user": {
            "id": created_user["id"],
            "name": created_user["name"],
            "email": created_user["email"],
            "role": created_user["role"]
        }
    }


# =========================================================
# 15. LOGIN
# =========================================================

@app.post("/login")
def login(user: LoginRequest):

    # Find user by email

    response = (
        supabase
        .table("users")
        .select("*")
        .eq("email", user.email)
        .execute()
    )

    if not response.data:

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    db_user = response.data[0]

    # Verify password

    password_valid = verify_password(
        user.password,
        db_user["password_hash"]
    )

    if not password_valid:

        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    # Create JWT

    access_token = create_access_token(
        user_id=db_user["id"],
        email=db_user["email"],
        role=db_user["role"]
    )

    return {
        "message": "Login successful",
        "access_token": access_token,
        "token_type": "bearer",
        "user": {
            "id": db_user["id"],
            "name": db_user["name"],
            "email": db_user["email"],
            "role": db_user["role"]
        }
    }


# =========================================================
# 16. CURRENT USER PROFILE
# =========================================================

@app.get("/me")
def get_my_profile(
    current_user: dict = Depends(get_current_user)
):

    return {
        "message": "Authentication successful",
        "user": current_user
    }


# =========================================================
# 17. CREATE BUG
# =========================================================
# Tester + Developer + Admin can create bugs

@app.post("/bugs")
def create_bug(
    bug: BugCreate,
    current_user: dict = Depends(require_roles("admin"))
):

    data = {
        "title": bug.title,
        "description": bug.description,
        "priority": bug.priority,
        "status": bug.status,
        "assigned_to": bug.assigned_to,

        # Automatically take creator from JWT
        "created_by": str(current_user["id"])
    }

    response = (
        supabase
        .table("bugs")
        .insert(data)
        .execute()
    )

    return {
        "message": "Bug created successfully",
        "bug": response.data
    }


# =========================================================
# 18. GET ALL BUGS
# =========================================================
# All authenticated users can view bugs

@app.get("/bugs")
def get_bugs(
    status: Optional[str] = None,
    priority: Optional[str] = None,
    current_user: dict = Depends(get_current_user)
):

    query = (
        supabase
        .table("bugs")
        .select("*")
    )

    if status:

        query = query.eq(
            "status",
            status
        )

    if priority:

        query = query.eq(
            "priority",
            priority
        )

    response = query.execute()

    return {
        "count": len(response.data),
        "bugs": response.data
    }


# =========================================================
# 19. GET ONE BUG
# =========================================================
# All authenticated users can view a bug

@app.get("/bugs/{bug_id}")
def get_bug(
    bug_id: int,
    current_user: dict = Depends(get_current_user)
):

    response = (
        supabase
        .table("bugs")
        .select("*")
        .eq("id", bug_id)
        .execute()
    )

    if not response.data:

        raise HTTPException(
            status_code=404,
            detail="Bug not found"
        )

    return response.data[0]


# =========================================================
# 20. UPDATE BUG
# =========================================================
# Developer + Admin can update bugs

@app.put("/bugs/{bug_id}")
def update_bug(
    bug_id: int,
    bug: BugUpdate,
    current_user: dict = Depends(
        require_roles("admin", "developer")
    )
):

    update_data = bug.model_dump(
        exclude_unset=True
    )

    if not update_data:

        raise HTTPException(
            status_code=400,
            detail="No data provided for update"
        )

    response = (
        supabase
        .table("bugs")
        .update(update_data)
        .eq("id", bug_id)
        .execute()
    )

    if not response.data:

        raise HTTPException(
            status_code=404,
            detail="Bug not found"
        )

    return {
        "message": "Bug updated successfully",
        "bug": response.data
    }


# =========================================================
# 21. DELETE BUG
# =========================================================
# Only Admin can delete bugs

@app.delete("/bugs/{bug_id}")
def delete_bug(
    bug_id: int,
    current_user: dict = Depends(
        require_roles("admin")
    )
):

    response = (
        supabase
        .table("bugs")
        .delete()
        .eq("id", bug_id)
        .execute()
    )

    if not response.data:

        raise HTTPException(
            status_code=404,
            detail="Bug not found"
        )

    return {
        "message": "Bug deleted successfully"
    }


# =========================================================
# 22. SEARCH BUGS
# =========================================================
# All authenticated users can search

@app.get("/search")
def search_bugs(
    keyword: str,
    current_user: dict = Depends(get_current_user)
):

    response = (
        supabase
        .table("bugs")
        .select("*")
        .ilike(
            "title",
            f"%{keyword}%"
        )
        .execute()
    )

    return {
        "count": len(response.data),
        "bugs": response.data
    }
@app.delete("/bugs/{bug_id}")
def delete_bug(
    bug_id: int,
    current_user: dict = Depends(get_current_user)
):
    if current_user["email"].lower() != "preetam@gmail.com":
        raise HTTPException(
            status_code=403,
            detail="Only admin can delete bugs."
        )

    response = supabase.table("bugs").delete().eq(
        "id", bug_id
    ).execute()

    if not response.data:
        raise HTTPException(
            status_code=404,
            detail="Bug not found"
        )

    return {
        "message": "Bug deleted successfully",
        "bug": response.data[0]
    }