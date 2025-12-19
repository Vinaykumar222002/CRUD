from fastapi import APIRouter, Request, Form, Depends, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from jose import jwt, JWTError
from passlib.context import CryptContext
from datetime import datetime, timedelta
from db import get_connection

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# JWT config
SECRET_KEY = "CHANGE_THIS_TO_A_LONG_RANDOM_SECRET"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
MAX_PASSWORD_LENGTH = 72

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str):
    if len(password.encode("utf-8")) > MAX_PASSWORD_LENGTH:
        raise ValueError("Password too long (max 72 characters)")
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str):
    return pwd_context.verify(plain, hashed)

def create_access_token(email: str):
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode = {"sub": email, "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def decode_token(token: str):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        return None

async def get_current_user(request: Request):
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    email = decode_token(token)
    if not email:
        raise HTTPException(status_code=401, detail="Invalid token")
    return email


# Signup page
@router.get("/signup")
def signup_page(request: Request):
    return templates.TemplateResponse("signup.html", {"request": request})

# Signup logic
@router.post("/signup")
def signup(email: str = Form(...), password: str = Form(...)):
    if len(password.encode("utf-8")) > MAX_PASSWORD_LENGTH:
        return RedirectResponse(url="/signup?msg=Password too long (max 72 characters)", status_code=303)

    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM auth_users WHERE email=%s", (email,))
    if cur.fetchone():
        cur.close()
        conn.close()
        return RedirectResponse(url="/signup?msg=User already exists", status_code=303)

    try:
        hashed_pw = hash_password(password)
        cur.execute("INSERT INTO auth_users (email, hashed_password) VALUES (%s, %s)", (email, hashed_pw))
        conn.commit()
    except Exception as e:
        conn.rollback()
        print("Error saving user:", e)
        return RedirectResponse(url="/signup?msg=Error saving user", status_code=303)
    finally:
        cur.close()
        conn.close()

    return RedirectResponse(url="/login?msg=Signup successful", status_code=303)

# Login page
@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

# Login logic
@router.post("/login")
def login(request: Request, email: str = Form(...), password: str = Form(...)):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, hashed_password FROM auth_users WHERE email=%s", (email,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row or not verify_password(password, row[1]):
        return RedirectResponse(url="/login?msg=Invalid credentials", status_code=303)

    token = create_access_token(email)
    response = RedirectResponse(url="/home/", status_code=303)
    response.set_cookie(key="access_token", value=token, httponly=True)
    return response

# Logout logic
@router.post("/logout")
def logout():
    response = RedirectResponse(url="/login?msg=Logged out", status_code=303)
    response.delete_cookie("access_token")
    return response

