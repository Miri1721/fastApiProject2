from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from passlib.context import CryptContext

app = FastAPI()
templates = Jinja2Templates(directory="templates")
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class User(BaseModel):
    username: str
    password: str


# In a real application, you'll store users in a database.
users_db = {}  # Temporary in-memory storage
@app.get("/register/")
async def show_register_form(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.post("/register/")
async def register(username: str = Form(...), password: str = Form(...)):
    user = User(username=username, password=password)
    hashed_password = pwd_context.hash(user.password)
    if user.username in users_db:
        raise HTTPException(status_code=400, detail="Username already exists")
    users_db[user.username] = hashed_password
    return {"status": "success", "username": user.username}