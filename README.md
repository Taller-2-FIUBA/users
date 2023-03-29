# users

Service to interact with users.

To start, run:

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

Once everything's set up, you can test the app. There's three main functionalities. First two are accessed
through localhost:8001 (frontend), last one through localhost:8000 (backend).

**New user sign up**

Using **new-signup/** you can add a new user with the following details

- password
- user itself (email, name, surname)

This will store the user in Firebase and populate the users database in the backend with its details and the
ID acquired from Firebase.

**Getting user details**

Using **get-user-details/** you can get an user's details by specifying

- email
- password

This will query the backend with the proper ID (acquired from Firebase if the user is valid) and return
the profile details.


**Getting all users' details**

Using **get-all users/** you can get the details for all users currently present in the database.
