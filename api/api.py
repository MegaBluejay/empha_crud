from time import time
from hashlib import sha256
from datetime import datetime

from merge_args import merge_args
from flask.views import MethodView
from werkzeug.exceptions import Unauthorized, NotFound, Forbidden
from jose import jwt, JWTError

def _hash_string(s: str) -> str:
    return sha256(s.encode('utf8')).hexdigest()

def _current_timestamp():
    return int(time())

USERS = {
    'admin': {
        'user_id': 0,
        'username': 'admin',
        'pass_hash': _hash_string('mmm'),
        'is_active': True,
        'is_superuser': True,
    },
    'user': {
        'user_id': 1,
        'username': 'user',
        'pass_hash': _hash_string('mmm'),
        'is_active': True,
        'is_superuser': False,
    },
}

IDS = {
    0: 'admin',
    1: 'user',
}

maxid = 0

def write(user_id, user):
    user['user_id'] = user_id
    password = user.pop('password')
    user['pass_hash'] =_hash_string(password)
    return user

def read(user):
    user = user.copy()
    del user['pass_hash']
    return user

JWT_SECRET = 'changeme' # todo
JWT_LIFETIME = 60*10
JWT_ALGORITHM = 'HS256'

def api_token_create(body):
    username = body['username']
    password = body['password']
    pass_hash = _hash_string(password)
    user = USERS.get(username, None)
    if not user or not user['is_active'] or user['pass_hash'] != pass_hash:
        raise Unauthorized
    user_id = user['user_id']
    timestamp = _current_timestamp()
    user['last_login'] = datetime.fromtimestamp(timestamp)
    payload = {
        'iat': timestamp,
        'exp': timestamp + JWT_LIFETIME,
        'sub': str(user_id),
    }
    return {'token': jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)}

def _id_is_active(user_id):
    username = IDS.get(user_id, None)
    return username and USERS[username]['is_active']

def api_token_decode(token):
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except JWTError as e:
        raise Unauthorized from e

def _auth_read(meth):
    @merge_args(meth)
    def wrapper(*args, user, **kwargs):
        current_user_id = int(user)
        if _id_is_active(current_user_id):
            return meth(*args, **kwargs)
        raise Unauthorized
    return wrapper

def _auth_write(meth):
    @merge_args(meth)
    def wrapper(*args, user, **kwargs):
        current_user_id = int(user)
        user_id = kwargs.get('user_id', None)
        if _id_is_active(current_user_id):
            current_user = USERS[IDS[current_user_id]]
            if current_user.get('is_superuser', False) or current_user_id == user_id:
                return meth(*args, **kwargs)
        raise Unauthorized
    return wrapper

class UsersView(MethodView):

    @_auth_read
    def get(self, user_id):
        if user_id not in IDS:
            raise NotFound
        return read(USERS[IDS[user_id]])

    @_auth_read
    def search(self):
        return [read(user) for user in USERS.values()]

    @_auth_write
    def post(self, body):
        global maxid
        maxid += 1
        user = write(maxid, body)
        username = user['username']
        if username in USERS:
            raise Forbidden
        IDS[maxid] = username
        USERS[username] = user
        return read(user)

    @_auth_write
    def put(self, user_id, body):
        if user_id not in IDS:
            raise NotFound
        user = write(user_id, body)
        username = user['username']
        old_username = IDS[user_id]
        if username != old_username and username in USERS:
            raise Forbidden
        del USERS[old_username]
        IDS[user_id] = username
        USERS[username] = user
        return read(user)

    @_auth_write
    def patch(self, user_id, body):
        if user_id not in IDS:
            raise NotFound
        user = write(user_id, body)
        old_username = IDS[user_id]
        username = user['username']
        if username != old_username and username in USERS:
            raise Forbidden
        USERS[old_username].update(user)
        if username != old_username:
            USERS[username] = USERS[old_username]
            del USERS[old_username]
            IDS[user_id] = username
        return read(USERS[username])

    @_auth_write
    def delete(self, user_id):
        if user_id not in IDS:
            raise NotFound
        del USERS[IDS[user_id]]
        del IDS[user_id]
