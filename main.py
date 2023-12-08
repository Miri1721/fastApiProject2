from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from passlib.context import CryptContext
from pymongo import MongoClient
from authlib.integrations.starlette_client import OAuth
from starlette.middleware.sessions import SessionMiddleware

app = FastAPI()

# Add session support for Authlib
app.add_middleware(SessionMiddleware, secret_key="some-random-secret")

oauth = OAuth()
templates = Jinja2Templates(directory="templates")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

google_oauth = oauth.register(
    name='google',
    client_id='1084050184657-4d98m97f175fr9mf3ij1d25umq9js6t5.apps.googleusercontent.com',
    client_secret='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',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    redirect_url='http://localhost:8000/login/callback',
    client_kwargs={'scope': 'openid profile email'},
)

class User(BaseModel):
    username: str
    email: str
    password: str


client = MongoClient("mongodb://localhost:27017/")
db = client["user_database"]
users = db["users"]


@app.get("/login-register")
async def login_register(request: Request):
    return templates.TemplateResponse("login_register.html", {"request": request})


@app.post("/register/")
async def register(username: str = Form(...), email: str = Form(...), password: str = Form(...), confirm_password: str = Form(...)):
    if password != confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    user = User(username=username, email=email, password=password)
    hashed_password = pwd_context.hash(user.password)

    if users.find_one({"username": username}):
        raise HTTPException(status_code=400, detail="Username already exists")

    users.insert_one({"username": username, "email": email, "password": hashed_password})
    return {"status": "success", "username": user.username}


@app.get("/login")
async def login(request: Request):
    # Use the same redirect URI
    return await google_oauth.authorize_redirect(request, 'http://localhost:8000/login/callback')

@app.get("/auth")
async def auth(request: Request):
    token = await google_oauth.authorize_access_token(request)
    user = await google_oauth.parse_id_token(request, token)
    return {"email": user['email'], "username": user['name']}


@app.get("/login/callback")
async def login_callback(request: Request):
    token = await google_oauth.authorize_access_token(request)
    user_info = await google_oauth.parse_id_token(request, token)
    # Here, you can check if the user exists in your database and register/login them accordingly.
    return user_info


@app.post("/local-login/")
async def local_login(username: str = Form(...), password: str = Form(...)):
    user = users.find_one({"username": username})
    if user and pwd_context.verify(password, user['password']):
        # Logic for successful local login
        return {"status": "success", "username": username}
    else:
        raise HTTPException(status_code=401, detail="Invalid username or password")

