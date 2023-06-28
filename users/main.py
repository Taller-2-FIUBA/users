"""Define all endpoints here."""
import json
import logging
import os
import time
from typing import List, Optional
import httpx

from fastapi import FastAPI, HTTPException, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.applications import get_swagger_ui_html
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from environ import to_config
from newrelic.agent import (
    record_custom_metric as record_metric,
    register_application,
)
from users.config import AppConfig
from users.database import get_database_url
from users.crud import (
    create_user,
    get_all_users,
    get_user_by_id,
    get_user_by_username,
    get_users_by_id,
    update_user,
    change_blocked_status,
    get_user_by_email,
    get_users_followed_by,
    unfollow_user,
    follow_new_user, get_wallet_details,
    get_followers, add_transaction, get_all_transactions,
    user_is_blocked, is_athlete, delete_user
)
from users.metrics import queue
from users.mongodb import (
    get_mongo_url,
    get_mongodb_connection,
    get_users_within,
    initialize
)
from users.payment.dto import BalanceBonus
from users.schemas import UserCreate, UserUpdate, UserBase, Location
from users.models import Base
from users.admin.dao import create_admin, get_all as get_all_admins
from users.admin.dto import AdminCreationDTO
from users.util import get_auth_header, get_credentials, \
    get_token, add_user_firebase, token_login_firebase, \
    create_wallet, upload_image, download_image, get_balance, \
    transfer_money_outside, deposit_money, add_to_balance
from users.healthcheck import HealthCheckDto
from users.location_helper import (
    get_coordinates,
    get_user_ids,
    save_location,
)

BASE_URI = "/users"
CONFIGURATION = to_config(AppConfig)
DOCUMENTATION_URI = BASE_URI + "/documentation/"
START = time.time()
MONGO_URL = get_mongo_url(CONFIGURATION)

logging.basicConfig(encoding="utf-8", level=CONFIGURATION.log_level.upper())
app = FastAPI(
    debug=CONFIGURATION.log_level.upper() == "DEBUG",
    openapi_url=DOCUMENTATION_URI + "openapi.json",
)

METHODS = [
    "GET",
    "get",
    "POST",
    "post",
    "PUT",
    "put",
    "PATCH",
    "patch",
    "OPTIONS",
    "options",
    "DELETE",
    "delete",
    "HEAD",
    "head",
]
ORIGIN_REGEX = "(http)?(s)?(://)?(.*vercel.app|localhost|local)(:3000)?.*"
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=ORIGIN_REGEX,
    allow_credentials=True,
    allow_methods=METHODS,
    allow_headers=['*']
)

NR_APP = register_application()
COUNTER = {"count": 1}

# Database initialization.
# Maybe move this, so it is only run when required? Now it runs when ever
# the application is started, and we may not need to create the database
# structure.
ENGINE = create_engine(get_database_url(CONFIGURATION),
                       pool_pre_ping=True, )
if "TESTING" not in os.environ:
    logging.info("Building database...")
    Base.metadata.create_all(bind=ENGINE)
    initialize(get_mongodb_connection(MONGO_URL))


# Helper methods, move somewhere else
def get_db() -> Session:
    """Create a session."""
    return Session(autocommit=False, autoflush=False, bind=ENGINE)


# Endpoint definition
@app.post("/users/login")
async def login(request: Request, session: Session = Depends(get_db)):
    """Log in to Firebase with email, password. Return token if successful."""
    record_metric('Custom/users-login/post', COUNTER, NR_APP)
    logging.info("Log-in user %s...")
    req = await request.json()
    email = req["email"]
    body = await token_login_firebase(request, "user", session)
    if user_is_blocked(session, email):
        raise HTTPException(status_code=401, detail="User is blocked")
    queue(CONFIGURATION, "user_login_count", "using_email_password")
    return JSONResponse(content=body, status_code=200)


def validate_user(session: Session, user: UserBase):
    """Create new user in the database based on id and user details."""
    logging.info("Validating user...")
    with session as open_session:
        db_user = get_user_by_email(open_session, email=user.email)
        if db_user:
            msg = "User with that email already present"
            logging.warning("Error creating user: %s", msg)
            raise HTTPException(status_code=400, detail=msg)
        db_user = get_user_by_username(open_session, username=user.username)
        if db_user:
            msg = "User with that username already present"
            logging.warning("Error creating user: %s", msg)
            raise HTTPException(status_code=400, detail=msg)


@app.post("/users")
async def create(new_user: UserCreate, session: Session = Depends(get_db)):
    """Create new user in Firebase, add it to the database if successful."""
    logging.info("Creating user %s...", new_user)
    record_metric('Custom/users/post', COUNTER, NR_APP)
    if new_user.email is None or new_user.password is None:
        msg = {'message': 'Error! Missing Email or Password'}
        logging.warning(
            "Error creating user: %s password: %s",
            new_user.email, new_user.password
        )
        raise HTTPException(detail=msg, status_code=400)
    validate_user(session, new_user)
    await add_user_firebase(new_user.email, new_user.password)
    wallet = await create_wallet()
    logging.debug("Creating user in DB...")
    if new_user.image:
        logging.info("Uploading user image...")
        await upload_image(new_user.image, new_user.username)
    db_user = create_user(session=session, user=new_user, wallet=wallet)
    try:
        save_location(
            MONGO_URL,
            db_user.is_athlete,
            db_user.id,
            new_user.coordinates,
            CONFIGURATION
        )
    except Exception as exc:
        delete_user(session, db_user.id)
        raise HTTPException(detail="MongoDB error when saving location",
                            status_code=500) from exc
    queue(CONFIGURATION, "user_created_count", "using_email_password")
    if new_user.location:
        queue(CONFIGURATION, "user_by_region_count", new_user.location)
    return db_user


async def validate_idp_token(request: Request):
    """Validate IDP Token through auth microservice."""
    logging.debug("Validating IDP token...")
    auth_header = get_auth_header(request)
    if auth_header is None:
        msg = "Missing IDP token"
        raise HTTPException(detail=msg, status_code=400)
    request = await request.json()
    url = f"http://{CONFIGURATION.auth.host}/auth/loginIDP"
    logging.info("Validating IDP token '%s' in '%s'", auth_header, url)
    res = await httpx.AsyncClient().post(url, json=request,
                                         headers=auth_header)
    if res.status_code != 200:
        error = res.json()["Message"]
        logging.error("Error when trying to login with IDP token: %s", error)
        raise HTTPException(status_code=res.status_code, detail=error)


@app.post("/users/usersIDP")
async def create_idp_user(request: Request,
                          user: UserBase, session: Session = Depends(get_db)):
    """Create new user with federated identity in database."""
    logging.info("Creating user with IDP token...")
    record_metric('Custom/users-usersIDP/post', COUNTER, NR_APP)
    if user.email is None:
        msg = {'message': 'Error! Missing Email'}
        raise HTTPException(detail=msg, status_code=400)
    validate_user(session, user)
    await validate_idp_token(request)
    wallet = await create_wallet()
    logging.debug("Creating IDP user in DB...")
    db_user = create_user(session=session, user=user, wallet=wallet)
    try:
        save_location(
            MONGO_URL,
            db_user.is_athlete,
            db_user.id,
            user.coordinates,
            CONFIGURATION
        )
    except Exception as exc:
        delete_user(session, db_user.id)
        raise HTTPException(detail="MongoDB error when saving location",
                            status_code=500) from exc
    queue(CONFIGURATION, "user_created_count", "using_idp")
    return db_user


@app.post("/users/login/usersIDP")
async def login_idp(request: Request, session: Session = Depends(get_db)):
    """Verify user is logged in through IDP and return token."""
    logging.info("Log-in user with IDP token...")
    record_metric('Custom/users-login-usersIDP/post', COUNTER, NR_APP)
    await validate_idp_token(request)
    request = await request.json()
    with session as open_session:
        user = get_user_by_email(session=open_session, email=request["email"])
        if user is None:
            msg = {'message': 'No IDP user with such an email'}
            logging.warning("Could not login with IDP token: %s", msg)
            raise HTTPException(detail=msg, status_code=404)
    queue(CONFIGURATION, "user_login_count", "using_idp")
    return {"token": await get_token("user", user.id), "id": user.id}


# pylint: disable=too-many-arguments
@app.get("/users/transactions")
async def get_transactions(
    request: Request,
    wallet_address: Optional[str] = None,
    minimum: Optional[float] = 0.0,
    offset: Optional[int] = 0,
    limit: Optional[int] = 10,
    session: Session = Depends(get_db)
):
    """Get all transactions."""
    record_metric('Custom/users-transactions/get', COUNTER, NR_APP)
    token = await get_credentials(request)
    if token["role"] != "admin":
        logging.warning("Invalid credentials for requesting all transactions")
        raise HTTPException(status_code=403, detail="Invalid credentials")
    with session as open_session:
        body = get_all_transactions(open_session,
                                    wallet_address,
                                    minimum,
                                    limit,
                                    offset)
        return body


@app.get("/users/{_id}")
async def get_one(
    request: Request,
    _id: int,
    session: Session = Depends(get_db)
):
    """Retrieve details for users with specified id."""
    logging.info("Retrieving user %d details...", _id)
    record_metric('Custom/users-id/get', COUNTER, NR_APP)
    token = await get_credentials(request)
    if not token["role"] == "admin" and not token["role"] == "user":
        logging.warning("Invalid role %s", token["role"])
        raise HTTPException(status_code=403, detail="Invalid credentials")
    with session as open_session:
        db_user = get_user_by_id(open_session, user_id=_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user


@app.get("/users/{user_id}/wallet")
async def get_user_wallet(
    request: Request,
    user_id: int,
    session: Session = Depends(get_db)
):
    """Retrieve wallet for users with specified id."""
    logging.info("Getting wallet belonging to user %d ...", user_id)
    record_metric('Custom/users-id-wallet/get', COUNTER, NR_APP)
    token = await get_credentials(request)
    if token["role"] != "user" or token["id"] != user_id:
        logging.warning("Invalid wallet access for user %d", user_id)
        raise HTTPException(status_code=403, detail="Invalid credentials")
    with session as open_session:
        wallet = get_wallet_details(open_session, user_id=user_id)
        if wallet.user_id != token["id"]:
            logging.warning("Invalid wallet access for user %d", user_id)
            raise HTTPException(status_code=403, detail="Invalid credentials")
        body = {
            "address": wallet.address,
            "private_key": wallet.private_key
        }
        return JSONResponse(content=body, status_code=200)


@app.get("/users/{user_id}/wallet/balance")
async def get_wallet_balance(
    request: Request,
    user_id: int,
    session: Session = Depends(get_db)
):
    """Retrieve wallet balance for user with specified id."""
    logging.info("Getting wallet balance belonging to user %d ...", user_id)
    record_metric('Custom/users-id-wallet-balance/get', COUNTER, NR_APP)
    token = await get_credentials(request)
    if token["id"] != user_id and token["role"] == "user":
        logging.warning("Invalid wallet access for user %d", user_id)
        raise HTTPException(status_code=403, detail="Invalid credentials")
    with session as open_session:
        wallet = get_wallet_details(open_session, user_id=user_id)
        if wallet is None:
            logging.warning("Non existent wallet")
            raise HTTPException(status_code=404, detail="Non existent wallet")
        balance = await get_balance(wallet)
        body = {
            "balance": balance,
        }
    return JSONResponse(content=body, status_code=200)


@app.post("/users/deposit")
async def make_payment(
    request: Request,
    session: Session = Depends(get_db)
):
    """Transfer specified money amount between specified users."""
    record_metric('Custom/users-deposit/post', COUNTER, NR_APP)
    req = await request.json()
    receiver_id = req["receiver_id"]
    sender_id = req["sender_id"]
    amount = req["amount"]
    token = await get_credentials(request)
    if token["id"] != sender_id or token["role"] != "user":
        logging.warning("Invalid wallet access for user %d", sender_id)
        raise HTTPException(status_code=403, detail="Invalid credentials")
    if not is_athlete(session, sender_id) or is_athlete(session,
                                                        receiver_id):
        logging.warning("Invalid transfer from user %d", sender_id)
        raise HTTPException(status_code=403, detail="Invalid transfer")
    with session as open_session:
        sender_wallet = get_wallet_details(open_session, user_id=sender_id)
        receiver_wallet = get_wallet_details(open_session, user_id=receiver_id)
        await deposit_money(sender_wallet, receiver_wallet, amount)
        add_transaction(session, sender_wallet.address,
                        receiver_wallet.address, amount)
        return JSONResponse(content={}, status_code=200)


@app.post("/users/extraction")
async def make_outside_payment(
    request: Request,
    session: Session = Depends(get_db)
):
    """Transfer specified money amount to an outside account."""
    record_metric('Custom/users-extraction/post', COUNTER, NR_APP)
    req = await request.json()
    receiver_address = req["receiver_address"]
    sender_id = req["sender_id"]
    amount = req["amount"]
    token = await get_credentials(request)
    if token["id"] != sender_id or token["role"] != "user":
        logging.warning("Invalid wallet access for user %d", sender_id)
        raise HTTPException(status_code=403, detail="Invalid credentials")
    with session as open_session:
        sender_wallet = get_wallet_details(open_session, user_id=sender_id)
        await transfer_money_outside(sender_wallet, receiver_address, amount)
        add_transaction(session, sender_wallet.address,
                        receiver_address, amount)
        return JSONResponse(content={}, status_code=200)


@app.patch("/users/status/{_id}")
async def change_status(request: Request,
                        _id: int,
                        session: Session = Depends(get_db)):
    """Invert blocked status of a user.

    Only admins allowed, can't block other admins
    """
    logging.info("Changing user %d status...", _id)
    record_metric('Custom/users-status-id/patch', COUNTER, NR_APP)
    token = await get_credentials(request)
    if not token["role"] == "admin":
        logging.warning("Invalid role %s", token["role"])
        raise HTTPException(status_code=403, detail="Invalid credentials")
    with session as open_session:
        db_user = get_user_by_id(open_session, user_id=_id)
        if not db_user.is_blocked:
            queue(CONFIGURATION, "user_blocked_count", None)
        change_blocked_status(open_session, _id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")


@app.patch("/users/{_id}")
async def patch_user(
    request: Request,
    _id: int,
    user: UserUpdate,
    session: Session = Depends(get_db)
):
    """Update user data."""
    record_metric('Custom/users-id/patch', COUNTER, NR_APP)
    logging.info("Updating user %d status...", _id)
    token = await get_credentials(request)
    if token["role"] == "user" and token["id"] != _id:
        logging.warning("Invalid role %s", token["role"])
        raise HTTPException(status_code=403, detail="Invalid credentials")
    with session as open_session:
        db_user = get_user_by_id(open_session, user_id=_id)
        if db_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
            )
        update_user(session, _id, user)
        if user.coordinates:
            save_location(
                MONGO_URL,
                db_user.is_athlete,
                _id,
                user.coordinates,
                CONFIGURATION,
            )
    return JSONResponse(content={}, status_code=200)


@app.patch("/users/{user_id}/wallet/balance")
async def add_balance(
    request: Request,
    body: BalanceBonus,
    user_id: int,
    session: Session = Depends(get_db)
):
    """Add balance to a user wallet."""
    logging.info("Creating admin...")
    record_metric('Custom/users-id-wallet-balance/patch', COUNTER, NR_APP)
    token = await get_credentials(request)
    if token["role"] != "admin":
        logging.warning("Invalid credentials for balance modification")
        raise HTTPException(status_code=403, detail="Invalid credentials")
    with session as open_session:
        receiver_wallet = get_wallet_details(open_session, user_id=user_id)
        await add_to_balance(receiver_wallet, body.amount)
        return JSONResponse(content={}, status_code=200)


# pylint: disable=too-many-arguments
@app.get("/users")
async def get_all(
    username: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
    radius: Optional[int] = 1000,
    offset: Optional[int] = 0,
    limit: Optional[int] = 10,
    session: Session = Depends(get_db),
):
    """Retrieve details for all users matching a search criteria."""
    logging.info(
        "Retrieving users, using filters: username='%s' latitude='%s' "
        "longitude='%s' radius='%s' offset='%s' limit='%s'",
        username, latitude, longitude, radius, offset, limit
    )
    record_metric('Custom/users/get', COUNTER, NR_APP)
    coordinates = get_coordinates(longitude, latitude)
    if username and coordinates:
        raise HTTPException(
            status_code=status.HTTP_406_NOT_ACCEPTABLE,
            detail="Can't search by username and location. Use only one."
        )
    with session as open_session:
        if username is None and coordinates is None:
            logging.info("Retrieving all users...")
            return get_all_users(open_session, limit=limit, offset=offset)
        if coordinates:
            user_ids = get_users_within(
                get_mongodb_connection(MONGO_URL), coordinates, radius
            )
            logging.debug("Found %s trainer IDs close to position.", user_ids)
            logging.info("Retrieving trainer data...")
            return get_users_by_id(
                open_session, get_user_ids(user_ids), limit, offset
            )
        logging.info("Retrieving user by name...")
        db_user = get_user_by_username(open_session, username=username)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    if username is not None:
        image = await download_image(username)
        if image:
            db_user.update(image)
    return db_user


@app.post("/users/recovery/{username}")
async def password_recovery(username: str, session: Session = Depends(get_db)):
    """Request auth service to start password recovery for user_id."""
    logging.info("Recovering password for user %s...", username)
    record_metric('Custom/users-recover-username/post', COUNTER, NR_APP)
    with session as open_session:
        db_user = get_user_by_username(session=open_session, username=username)
        if db_user is None:
            raise HTTPException(status_code=404, detail="User not found")
    url = f"http://{CONFIGURATION.auth.host}/auth/recovery?email=" + \
          db_user["email"] + "&username=" + username
    logging.info("Requesting password recovery to %s...", url)
    res = await httpx.AsyncClient().post(url)
    if res.status_code != 200:
        error = res.json()["Message"]
        logging.error("Error when recovering password: %s", error)
        raise HTTPException(status_code=res.status_code, detail=error)
    queue(CONFIGURATION, "user_password_recovery_count", None)
    return JSONResponse(content={}, status_code=200)


@app.get("/users/{user_id}/followed")
async def get_followed_users(
    user_id: int,
    session: Session = Depends(get_db)
):
    """Retrieve all users followed by user with specified id."""
    logging.info("Getting followed users for user %s...", user_id)
    record_metric('Custom/users-id-followed/get', COUNTER, NR_APP)
    with session as open_session:
        db_user = get_user_by_id(open_session, user_id=user_id)
        if db_user is None:
            raise HTTPException(status_code=404, detail="User not found")
    return get_users_followed_by(session, user_id)


@app.get("/users/{user_id}/followers")
async def get_user_followers(
    user_id: int,
    session: Session = Depends(get_db)
):
    """Retrieve all users followed by user with specified id."""
    logging.info("Getting followers for user %s...", user_id)
    record_metric('Custom/users-id-followers/get', COUNTER, NR_APP)
    with session as open_session:
        db_user = get_user_by_id(open_session, user_id=user_id)
        if db_user is None:
            raise HTTPException(status_code=404, detail="User not found")
    return get_followers(session, user_id)


@app.delete("/users/{user_id}/followed/{_id}")
async def stop_following_user(
    request: Request,
    _id: int,
    user_id: int,
    session: Session = Depends(get_db)
):
    """Retrieve all users followed by user with specified id."""
    record_metric('Custom/users-id-followed-id/delete', COUNTER, NR_APP)
    with session as open_session:
        db_user = get_user_by_id(open_session, user_id=user_id)
        if db_user is None:
            raise HTTPException(status_code=404, detail="User not found")
    token = await get_credentials(request)
    if token["id"] != user_id:
        raise HTTPException(status_code=403, detail="Invalid credentials")
    return unfollow_user(session, user_id, _id)


@app.post("/users/{user_id}/followed/{_id}")
async def follow_user(
    request: Request,
    _id: int,
    user_id: int,
    session: Session = Depends(get_db)
):
    """Retrieve all users followed by user with specified id."""
    record_metric('Custom/users-id-followed-id/post', COUNTER, NR_APP)
    with session as open_session:
        db_user = get_user_by_id(open_session, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    token = await get_credentials(request)
    if token["id"] != user_id:
        raise HTTPException(status_code=403, detail="Invalid credentials")
    if _id == user_id:
        msg = "User can't follow himself"
        raise HTTPException(status_code=400, detail=msg)
    return follow_new_user(session, user_id, _id)


# Admin endpoints. Maybe move to their own module.
@app.post("/admins")
async def add_admin(
    new_admin: AdminCreationDTO,
    session: Session = Depends(get_db)
):
    """Create an admin."""
    logging.info("Creating admin...")
    record_metric('Custom/admins/post', COUNTER, NR_APP)
    if new_admin.email is None:
        msg = {'message': 'Error! Missing Email.'}
        raise HTTPException(detail=msg, status_code=400)
    if new_admin.password is None:
        msg = {'message': 'Error! Missing Password.'}
        raise HTTPException(detail=msg, status_code=400)
    await add_user_firebase(new_admin.email, new_admin.password)
    with session as open_session:
        return create_admin(open_session, new_admin)


@app.get("/admins")
async def get_admins(request: Request, session: Session = Depends(get_db)):
    """Return all administrators."""
    logging.info("Retrieving admins...")
    record_metric('Custom/admins/get', COUNTER, NR_APP)
    token = await get_credentials(request)
    if token["role"] != "admin":
        logging.warning("Invalid role %s", token["role"])
        raise HTTPException(status_code=403, detail="Invalid credentials")
    with session as open_session:
        return get_all_admins(open_session)


@app.post("/admins/login")
async def admin_login(request: Request, session: Session = Depends(get_db)):
    """Login as administrator. Return token if successful."""
    logging.info("Login admins...")
    record_metric('Custom/admins-login/post', COUNTER, NR_APP)
    body = await token_login_firebase(request, "admin", session)
    return JSONResponse(content=body, status_code=200)


@app.get(BASE_URI + "/healthcheck/")
async def health_check() -> HealthCheckDto:
    """Check for how long has the service been running."""
    return HealthCheckDto(uptime=time.time() - START)


@app.get(DOCUMENTATION_URI, include_in_schema=False)
async def custom_swagger_ui_html(req: Request):
    """To show Swagger with API documentation."""
    root_path = req.scope.get("root_path", "").rstrip("/")
    openapi_url = root_path + app.openapi_url
    return get_swagger_ui_html(
        openapi_url=openapi_url,
        title="FIUFIT users",
    )


@app.get(BASE_URI + "/locations/", response_model=List[Location])
async def get_locations() -> List[Location]:
    """Return CABA locations. Coordinates format (longitude, latitude)."""
    logging.info("Returning locations...")
    record_metric('Custom/users-locations/get', COUNTER, NR_APP)
    with open("static/location.json", encoding="UTF-8") as location_file:
        return json.load(location_file)
