# users

Service to interact with users.

## Virtual environment

Set up:

```bash
sudo apt install python3.11 python3.11-venv
python3.11 -m venv .
source venv/bin/activate
pip install pip --upgrade
pip install -r requirements.txt -r dev-requirements.txt
```

## FastAPI

```bash
uvicorn main:app --reload
```

## Tests

```bash
tox
```

## Docker

Building docker image:

```bash
docker build --tag IMAGE_NAME .
```

Where `IMAGE_NAME` is a name to identify the image later.

Then run the container:

```bash
docker run --rm -p 8080:80 --name CONTAINER_NAME IMAGE_NAME
```

Where `IMAGE_NAME` is the name chosen in the previous step and `CONTAINER_NAME`
is a name to identify the container running.  
Notice `--rm` tells docker to remove the container after exists, and
`-p 8080:80` maps the port 80 in the container to the port 8080 in the host.

