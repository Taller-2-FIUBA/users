"""Constants to use for testing."""

user_1 = {
    "password": "jorgito_pw",
    "username": "jorgitogroso",
    "email": "jorgitodd@asddbcdd.com",
    "name": "Jorge",
    "surname": "Perales",
    "height": 1.9,
    "weight": 100,
    "birth_date": "23-4-1990",
    "location": "Buenos Aires, Argentina",
    "registration_date": "23-4-2023",
    "is_athlete": True
}

idp_user_1 = {
    "username": "jorgitogroso",
    "email": "jorgitodd@asddbcdd.com",
    "name": "Jorge",
    "surname": "Perales",
    "height": 1.9,
    "weight": 100,
    "birth_date": "23-4-1990",
    "location": "Buenos Aires, Argentina",
    "registration_date": "23-4-2023",
    "is_athlete": True
}

idp_user_2 = {
    "username": "pepitobasura",
    "email": "pepitod@abcd.com",
    "name": "Pepo",
    "surname": "Gutierrez",
    "height": 1.8,
    "weight": 60,
    "birth_date": "23-4-1987",
    "location": "Rosario, Santa Fe",
    "registration_date": "23-3-2023",
    "is_athlete": False
}

private_keys = {
    "id",
    "password",
    "username",
    "height",
    "weight",
    "birth_date",
    "registration_date",
    "is_athlete",
    "is_blocked"
}

user_2 = {
    "password": "pepito_pw",
    "username": "pepitobasura",
    "email": "pepitod@abcd.com",
    "name": "Pepo",
    "surname": "Gutierrez",
    "height": 1.8,
    "weight": 60,
    "birth_date": "23-4-1987",
    "location": "Rosario, Santa Fe",
    "registration_date": "23-3-2023",
    "is_athlete": False
}

user_3 = {
    "password": "anita_pw",
    "username": "anitazoomer",
    "email": "anita@abcd.com",
    "name": "Ana",
    "surname": "Rodriguez",
    "height": 1.3,
    "weight": 80,
    "birth_date": "23-4-1999",
    "location": "Cordoba, Cordoba",
    "registration_date": "23-3-2022",
    "is_athlete": True
}

user_to_update = {
    "password": "pass22word1",
    "username": "old_username",
    "email": "ema1il12@abcd.com",
    "name": "old_name",
    "surname": "old_surname",
    "height": 1.1,
    "weight": 800,
    "birth_date": "23-4-1999",
    "location": "Cordoba, Cordoba",
    "registration_date": "23-3-2022",
    "is_athlete": True
}

user_to_update_location = {
    "password": "location",
    "username": "location",
    "email": "location@abcd.com",
    "name": "location",
    "surname": "location",
    "height": 1.1,
    "weight": 800,
    "birth_date": "23-4-1999",
    "location": "old_location",
    "registration_date": "23-3-2022",
    "is_athlete": True
}

user_template_no_email = {
    "password": "password",
    "name": "name",
    "surname": "surname",
    "height": 1.15,
    "weight": 300,
    "birth_date": "23-4-1995",
    "location": "Tierra del Fuego",
    "registration_date": "23-3-2023",
    "is_athlete": True
}

test_wallet = {
    "address": "test_address",
    "privateKey": "test_key"
}

test_wallet_1 = {
    "address": "test_address_1",
    "privateKey": "test_key_1"
}

test_wallet_2 = {
    "address": "test_address_2",
    "privateKey": "test_key_2"
}


def equal_dicts(dict1, dict2, ignore_keys):
    """Return true if dict1 equals dict2 minus ignore_keys."""
    d1_filtered = {k: v for k, v in dict1.items() if k not in ignore_keys}
    d2_filtered = {k: v for k, v in dict2.items() if k not in ignore_keys}
    return d1_filtered == d2_filtered
