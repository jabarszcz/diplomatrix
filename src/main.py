# Adapted from the matrix-nio examples
# https://github.com/poljar/matrix-nio/blob/master/examples/restore_login.py

import asyncio
import getpass
import json
import readline  # noqa : for 'input()'
import sys
from urllib.parse import urlsplit, urlunsplit

from nio import AsyncClient, LoginResponse

CREDS_FILE = "credentials.json"


def save_login(resp: LoginResponse, matrix_server) -> None:
    with open(CREDS_FILE, "w") as f:
        json.dump(
            {
                "homeserver": matrix_server,
                "user_id": resp.user_id,
                "device_id": resp.device_id,
                "access_token": resp.access_token,
            },
            f,
        )


async def login() -> None:
    try:
        with open(CREDS_FILE) as f:
            creds = json.load(f)
            client = AsyncClient(creds["homeserver"])
            client.access_token = creds["access_token"]
            client.user_id = creds["user_id"]
            client.device_id = creds["device_id"]
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        print(
            f"Did not find credentials in {CREDS_FILE}. "
            "Asking for login info."
        )
        matrix_server_str = "matrix.org"
        matrix_server_str = (
            input(
                "Enter your matrix server URL "
                f"(default = {matrix_server_str!r}): "
            )
            or matrix_server_str
        )

        url = urlsplit(matrix_server_str)
        url = (
            url._replace(scheme=url.scheme or "https")
            ._replace(netloc=url.netloc or url.path)
            ._replace(path="")
        )
        matrix_server = urlunsplit(url)

        user_id = input("Enter your user ID: ")
        user, *server_maybe = user_id.lstrip("@").split(":", 1)
        user_id = f"@{user}:" + (
            server_maybe[0] if server_maybe else url.netloc
        )

        device_name = "diplomatrix_client"
        device_name = (
            input(
                "Choose a name for this device "
                f"(default = {device_name!r}): "
            )
            or device_name
        )

        client = AsyncClient(matrix_server, user_id)
        pw = getpass.getpass()
        resp = await client.login(pw, device_name=device_name)

        if isinstance(resp, LoginResponse):
            save_login(resp, matrix_server)
            print(f"Logged in. Credentials saved to {CREDS_FILE!r}")
        else:
            print(f'server = "{matrix_server}"; user = "{user_id}"')
            print(f"Failed to log in: {resp}")
            sys.exit(1)

    await client.close()


asyncio.get_event_loop().run_until_complete(login())
