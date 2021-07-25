from time import time
from hashlib import sha256
from functools import wraps
from datetime import datetime
import inspect

from merge_args import merge_args
from flask.views import MethodView
from werkzeug.exceptions import Unauthorized, NotFound, Forbidden
from jose import jwt, JWTError
from addict import Dict
import dataset

db = dataset.connect(row_type=Dict, ensure_schema=False)
USERS : dataset.Table = db['users']

JWT_SECRET = 'changeme' # todo
JWT_LIFETIME = 60*10
JWT_ALGORITHM = 'HS256'


def _hash_string(s: str) -> str:
    return sha256(s.encode('utf8')).hexdigest()

def _id_is_active(user_id):
    user = USERS.find_one(user_id=user_id)
    return user and user.is_active

def _user_out(user):
    out = {}
    for attr, val in user.items():
        if attr.startswith('is_'):
            out[attr] = bool(val)
        elif attr != 'pass_hash' and val is not None:
            out[attr] = val
    return out

def _user_in(user):
    user.pass_hash = _hash_string(user.password)
    del user.password
    return user

def _auth_read(func):
    def wrapper(*args, user, token_info, **kwargs):
        current_user_id = int(user)
        if _id_is_active(current_user_id):
            return func(*args, **kwargs)
        raise Unauthorized
    return wrapper

def _auth_write(func):
    def wrapper(*args, user, token_info, **kwargs):
        current_user_id = int(user)
        user_id = kwargs.get('user_id', None)
        if _id_is_active(current_user_id):
            current_user = USERS.find_one(user_id=current_user_id)
            if current_user.get('is_superuser', False) or current_user_id == user_id:
                return func(*args, **kwargs)
        raise Unauthorized
    return wrapper

def _modded_body(func):
    def wrapper(*args, body, **kwargs):
        user = _user_in(Dict(body))
        if 'user_id' in kwargs:
            user.user_id = kwargs['user_id']
        return func(*args, body=user, **kwargs)
    return wrapper

@_modded_body
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

    @_auth_read
    def get(self, user_id):
        user = USERS.find_one(user_id=user_id)
        if not user:
            raise NotFound
        return _user_out(user)

    @_auth_read
    def search(self):
        return [_user_out(user) for user in USERS]

    @_auth_write
    @_modded_body
    def post(self, body):
        username = body.username
        if USERS.count(username=username):
            raise Forbidden
        body.user_id = USERS.insert(body)
        return _user_out(body), 201

    @_auth_write
    @_modded_body
    def put(self, user_id, body):
        user = USERS.find_one(user_id=user_id)
        if not user:
            raise NotFound
        if user.username != body.username and USERS.count(username=body.username):
            raise Forbidden
        for attr in ['first_name', 'last_name', 'last_login']:
            body.setdefault(attr, None)
        USERS.update(body, ['user_id'])
        return _user_out(body)

    @_auth_write
    @_modded_body
    def patch(self, user_id, body):
        user = USERS.find_one(user_id=user_id)
        if not user:
            raise NotFound
        if user.username != body.username and USERS.count(username=body.username):
            raise Forbidden
        USERS.update(body, ['user_id'])
        user.update(body)
        return _user_out(user)

    @_auth_write
    def delete(self, user_id):
        if not USERS.count(user_id=user_id):
            raise NotFound
        USERS.delete(user_id=user_id)
