
## Installation

Requirements:

- **Python 3.7+**
- PostgreSQL (tested using 9.6+)
- gifsicle for GIF emoji and avatar handling
- [pipenv]

[pipenv]: https://github.com/pypa/pipenv

### Setting up the database

It's recommended to create a separate user for the `discord` database.

```sh
# Create the PostgreSQL database.
$ createdb discord

# Apply the base schema to the database.
$ psql -f schema.sql discord
```

Then, you should run database migrations:

```sh
$ pipenv run ./manage.py migrate
```

### Configuring

Copy the `config.example.py` file and edit it to configure your instance:

```sh
$ cp config.example.py config.py
$ $EDITOR config.py
```

### Install packages

```sh
$ pipenv install --dev
```

## Running

Hypercorn is used to run Discord. By default, it will bind to `0.0.0.0:5000`.
This will expose your Discord instance to the world. You can use the `-b`
option to change it (e.g. `-b 0.0.0.0:45000`).

```sh
$ pipenv run hypercorn run:app
```

You can use `--access-log -` to output access logs to stdout.

**It is recommended to run discord behind [NGINX].** You can use the
`nginx.conf` file at the root of the repository as a template.

[nginx]: https://www.nginx.com

### Does it work?

You can check if your instance is running by performing an HTTP `GET` request on
the `/api/v6/gateway` endpoint. For basic websocket testing, a tool such as
[ws](https://github.com/hashrocket/ws) can be used.

## Updating

Update the code and run any new database migrations:

```sh
$ git pull
$ pipenv run ./manage.py migrate
```

## Running tests

Running tests involves creating dummy users with known passwords. Because of
this, you should never setup a testing environment in production.

```sh
# Setup any testing users:
$ pipenv run ./manage.py setup_tests

# Install tox:
$ pip install tox

# Run lints and tests:
$ tox
```
