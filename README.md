# users

Service to interact with users.

## Virtual environment

Set up:

```bash
sudo apt install python3.11 python3.11-venv
python3.11 -m venv venv
source venv/bin/activate
pip install pip --upgrade
pip install -r requirements.txt -r dev-requirements.txt
```

## Tests

```bash
tox
```

## Docker

There's a docker-composef file all set up, just run:

```
docker compose up
```
This will launch two dockerized containers in the same network (a PostgreSQL database and the app itself.)

And in a separate terminal (within _/users_)
```
uvicorn --port 8001 mock_frontend:app --reload
```
The only purpose of mock_frontend is to test the frontend's Firebase functionality, thats
why it's not *dockerized*.
