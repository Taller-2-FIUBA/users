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

# signup endpoint
# creates user from email and password, returns user id
@app.post("/signup", include_in_schema=False)
async def signup(request: Request):
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

# login endpoint
# returns jwt for valid user (correct email and password)
@app.post("/login", include_in_schema=False)
async def login(request: Request):
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
def signup(password: str, user: schemas.UserBase):
    body = {
        "email": user.email,
        "password": password
    }
    response = requests.post(url="http://localhost:8001/signup", json=body)
    if response.status_code == 200:
        id = json.loads(response.text)["id"]
        new_user_body = {
            "id": id,
            "email": user.email,
            "name": user.name,
            "surname": user.surname
        }
        requests.post(url="http://localhost:8000/new-signup", json=new_user_body)
    return response.text

@app.post("/get-user-details")
def user_details(password: str, email: str):
    body = {
        "email": email,
        "password": password
    }
    response = requests.post(url="http://localhost:8001/login", json=body)
    if response.status_code == 200:
        token = json.loads(response.text)["token"]
        user = auth.verify_id_token(token)
        body = {
            'id': user["uid"]
        }
        response = requests.get(url="http://localhost:8000/user-details", headers=body)
    return response.text

if __name__ == "__main__":
   uvicorn.run("main:app")
