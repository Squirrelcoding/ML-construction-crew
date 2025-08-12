from typing import Union

from fastapi import FastAPI
from pydantic import BaseModel

from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from passlib.context import CryptContext
from pydantic import BaseModel

import os
from supabase import create_client, Client

from dotenv import load_dotenv

load_dotenv(".env")

# to get a string like this run:
# openssl rand -hex 32
SECRET_KEY: str = os.environ.get("SECRET_KEY") #type: ignore
print(SECRET_KEY)
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: str | None = None

class User(BaseModel):
    username: str
    email: str | None = None
    disabled: bool | None = None

class FullUser(BaseModel):
    username: str
    email: str | None = None
    disabled: bool | None = None
    hashed_password: str  

class UserInDB(User):
    hashed_password: str


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

app = FastAPI()

class DBWrapper():
    def __init__(self, url: str, key: str) -> None:
        self.client: Client = create_client(url, key)
    def contains_username(self, username):
        response = self.client.table("users").select("*").eq("username", username).limit(1).execute()
        return len(response.data) > 0
    def get_user(self, username):
        response = self.client.table("users").select("*").eq("username", username).limit(1).execute()
        return response.data[0]
    def create_user(self, user: FullUser):
        if self.contains_username(user.username):
            return
        self.client.table("users").insert({
            "username": user.username,
            "hashed_password": user.hashed_password,
            "disabled": user.disabled
        }).execute()

url: str = os.environ.get("SUPABASE_URL") # type: ignore
key: str = os.environ.get("SUPABASE_KEY") #type: ignore
db = DBWrapper(url, key)

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def get_user(username: str):
    if db.contains_username(username):
        user_dict = db.get_user(username)
        return UserInDB(**user_dict)

def authenticate_user(username: str, password: str):
    user = get_user(username)
    if not user:
        return False
    
    if not verify_password(password, user.hashed_password):
        return False
    return user


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except InvalidTokenError:
        raise credentials_exception
    user = get_user(token_data.username) # type: ignore
    if user is None:
        raise credentials_exception
    return user


async def get_current_active_user(
    current_user: Annotated[User, Depends(get_current_user)],
):
    if current_user.disabled:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


@app.post("/token")
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return Token(access_token=access_token, token_type="bearer")

@app.post("/signup")
async def signup(form_data: Annotated[OAuth2PasswordRequestForm, Depends()]):
    hashed_password = pwd_context.hash(form_data.password)

    user = FullUser(
        username=form_data.username,
        hashed_password=hashed_password,
        disabled=False,
    )
    db.create_user(user)

@app.get("/users/models/")
async def get_models(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return [{"item_id": "Foo", "owner": current_user.username}]

@app.get("/users/datasets/")
async def get_datasets(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    return [{"item_id": "Foo", "owner": current_user.username}]


class ModelFactory:
    """
    A model factory that makes constructing PyTorch models easier by verifying that a new model is valid.
    """
    def __init__(self) -> None:
        self.layers = []
    def add_layer(self, layer):
        pass

class Item(BaseModel):
    name: str
    price: float
    is_offer: Union[bool, None] = None