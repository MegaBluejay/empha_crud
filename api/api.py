from datetime import datetime
from os import environ
from time import time

from addict import Dict
from flask.views import MethodView
from jose import jwt, JWTError
from werkzeug.exceptions import Unauthorized, NotFound, Forbidden

from db import connect_db
from ext import hash_string

__all__ = ['UsersView', 'api_token_create', 'api_token_decode']

JWT_SECRET = environ['JWT_SECRET']
JWT_LIFETIME = 60*10
JWT_ALGORITHM = 'HS256'

USERS = connect_db()['users']

def id_is_active(user_id):
    user = USERS.find_one(user_id=user_id)
    return user and user.is_active

def user_out(user):
    out = {}
    for attr, val in user.items():
        if attr.startswith('is_'):
            out[attr] = bool(val)
        elif attr != 'pass_hash' and val is not None:
            out[attr] = val
    return out

def user_in(user):
    user.pass_hash = hash_string(user.password)
    del user.password
    return user

def auth_read(func):
    def wrapper(*args, user, token_info, **kwargs):
        current_user_id = int(user)
        if id_is_active(current_user_id):
            return func(*args, **kwargs)
        raise Unauthorized
    return wrapper

def auth_write(func):
    def wrapper(*args, user, token_info, **kwargs):
        current_user_id = int(user)
        user_id = kwargs.get('user_id', None)
        if id_is_active(current_user_id):
            current_user = USERS.find_one(user_id=current_user_id)
            if current_user.get('is_superuser', False) or current_user_id == user_id:
                return func(*args, **kwargs)
        raise Unauthorized
    return wrapper

def modded_body(func):
    def wrapper(*args, body, **kwargs):
        user = user_in(Dict(body))
        if 'user_id' in kwargs:
            user.user_id = kwargs['user_id']
        return func(*args, body=user, **kwargs)
    return wrapper

@modded_body
def api_token_create(body):
    username = body.username
    user = USERS.find_one(username=username)
    if not user or not user.is_active or user.pass_hash != body.pass_hash:
        raise Unauthorized
    user_id = user.user_id
    timestamp = int(time())
    USERS.update(dict(user_id=user_id, last_login=datetime.now()), ['user_id'])
    payload = {
        'iat': timestamp,
        'exp': timestamp + JWT_LIFETIME,
        'sub': str(user_id),
    }
    return {'token': jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)}

def api_token_decode(token):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError as e:
        raise Unauthorized from e

class UsersView(MethodView):

    @auth_read
    def get(self, user_id):
        user = USERS.find_one(user_id=user_id)
        if not user:
            raise NotFound
        return user_out(user)

    @auth_read
    def search(self):
        return [user_out(user) for user in USERS]

    @auth_write
    @modded_body
    def post(self, body):
        username = body.username
        if USERS.count(username=username):
            raise Forbidden
        body.user_id = USERS.insert(body)
        return user_out(body), 201

    @auth_write
    @modded_body
    def put(self, user_id, body):
        user = USERS.find_one(user_id=user_id)
        if not user:
            raise NotFound
        if user.username != body.username and USERS.count(username=body.username):
            raise Forbidden
        for attr in ['first_name', 'last_name', 'last_login']:
            body.setdefault(attr, None)
        USERS.update(body, ['user_id'])
        return user_out(body)

    @auth_write
    @modded_body
    def patch(self, user_id, body):
        user = USERS.find_one(user_id=user_id)
        if not user:
            raise NotFound
        if user.username != body.username and USERS.count(username=body.username):
            raise Forbidden
        USERS.update(body, ['user_id'])
        user.update(body)
        return user_out(user)

    @auth_write
    def delete(self, user_id):
        if not USERS.count(user_id=user_id):
            raise NotFound
        USERS.delete(user_id=user_id)
