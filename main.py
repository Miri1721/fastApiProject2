from fastapi import FastAPI,Depends, HTTPException, Request, Form
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from passlib.context import CryptContext
from pymongo import MongoClient
from fastapi.security.oauth2 import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi_security_oauth.google import GoogleOAuth2
import httpx

app = FastAPI()
templates = Jinja2Templates(directory="templates")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class User(BaseModel):
    username: str
    password: str


# Connect to local MongoDB instance
client = MongoClient("mongodb://localhost:27017/")
# Create or access a database named 'user_database'
db = client["user_database"]
# Create or access a collection named 'users'
users = db["users"]

@app.get("/register/")
async def show_register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})


@app.post("/register/")
async def register(username: str = Form(...), password: str = Form(...)):
    user = User(username=username, password=password)
    hashed_password = pwd_context.hash(user.password)

    if users.find_one({"username": username}):
        raise HTTPException(status_code=400, detail="Username already exists")

    # Insert user data into the 'users' collection
    users.insert_one({"username": username, "password": hashed_password})

    return {"status": "success", "username": user.username}

# Initialize Google OAuth2
google_oauth2 = GoogleOAuth2("1084050184657-4d98m97f175fr9mf3ij1d25umq9js6t5.apps.googleusercontent.com", "GOCSpX-V5dWX-biAcrCVcmQmiFPtEX2KjqE")

@app.get("/login")
async def login(request: Request):
    return await google_oauth2.get_login_redirect(request)

@app.get("/login/callback")
async def login_callback(request: Request):
    token = await google_oauth2.get_access_token(request)
    user_info = await google_oauth2.get_user_info(token)
    # Here, user_info will contain information about the user. You can use this to authenticate or register the user in your system.
    # For now, we'll just return the user_info to see what it contains:
    return user_info