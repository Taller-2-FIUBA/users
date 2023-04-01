import firebase_admin
import uvicorn
import pyrebase
import json
import requests

from firebase_admin import credentials, auth
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import HTTPException

import schemas

# Only meant for testing. Delete after integration

cred = credentials.Certificate("backend-demo_service_account_keys.json")
firebase = firebase_admin.initialize_app(cred)
pb = pyrebase.initialize_app(json.load(open('../firebase_config.json')))

app = FastAPI()
allow_all = ['*']
app.add_middleware(
   CORSMiddleware,
   allow_origins=allow_all,
   allow_credentials=True,
   allow_methods=allow_all,
   allow_headers=allow_all
)


@app.post("/signup", include_in_schema=False)
async def signup(request: Request):
    """Creates user in Firebase from email and password, returns user_id"""
    req = await request.json()
    email = req['email']
    password = req['password']
    if email is None or password is None:
        raise HTTPException(detail={'message': 'Error! Missing Email or Password'}, status_code=400)
    try:
        user = auth.create_user(
            email=email,
            password=password
        )
        return JSONResponse(content={'id': user.uid}, status_code=200)
    except:
        raise HTTPException(detail={'message': 'Error Creating User'}, status_code=400)


@app.post("/login", include_in_schema=False)
async def login(request: Request):
    """Logs in to Firebase with email, password. Returns token if successful"""
    req_json = await request.json()
    email = req_json['email']
    password = req_json['password']
    try:
        user = pb.auth().sign_in_with_email_and_password(email, password)
        jwt = user['idToken']
        return JSONResponse(content={'token': jwt}, status_code=200)
    except:
        raise HTTPException(detail={'message': 'There was an error logging in'}, status_code=400)


@app.post("/new-signup")
def new_user(password: str, user: schemas.UserBase):
    """Creates new user, returns new user details if successful"""
    body = {
        "email": user.email,
        "password": password
    }
    response = requests.post(url="http://localhost:8001/signup", json=body)
    if response.status_code == 200:
        user_id = json.loads(response.text)["id"]
        new_user_details = {
            "email": user.email,
            "name": user.name,
            "surname": user.surname
        }
        requests.post(url="http://localhost:8000/users/"+user_id, json=new_user_details)
    return response.text


@app.get("/user")
def user_details(password: str, email: str):
    """Attempts to retrieve user details based on email and password.
    Returns user details if successful"""
    body = {
        "email": email,
        "password": password
    }
    response = requests.post(url="http://localhost:8001/login", json=body)
    if response.status_code == 200:
        token = json.loads(response.text)["token"]
        user = auth.verify_id_token(token)
        response = requests.get(url="http://localhost:8000/users/" + user["uid"])
    return response.text


if __name__ == "__main__":
    uvicorn.run("main:app")
