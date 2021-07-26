# Simple CRUD

## Installation

1. Clone this repository
2. Make a virtualenv (optional)
3. `pip3 install -r requirements.txt`

## Usage

### Environment variables

`DATABASE_URL`, e.g. `mysql://user:pass@localhost/db`

`JWT_TOKEN`, a string, will be used to sign tokens

Optional: `INIT_DB`, either 0 or 1, default 0. When set to 1 will initialize a table to be used by the app

To use an in-memory sqlite database set:

```
DATABASE_URL='sqlite:///file:db?mode=memory&cache=shared&uri=true'
INIT_DB=1
```

### Running

`python crud.py`
