"""A shared password in front of a hosted Halo, so a found link can't spend your Claude credits."""

import base64
import binascii
import secrets


class PasswordGate:
    """HTTP Basic auth with one password and any user name; browsers show their own login box."""

    def __init__(self, app, password: str, open_paths: frozenset[str] = frozenset()):
        self.app = app
        self.password = password.encode()
        self.open_paths = open_paths

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http" or scope["path"] in self.open_paths or self._authorized(scope):
            await self.app(scope, receive, send)
            return
        await send({
            "type": "http.response.start",
            "status": 401,
            "headers": [
                (b"www-authenticate", b'Basic realm="Halo", charset="UTF-8"'),
                (b"content-type", b"text/plain; charset=utf-8"),
            ],
        })
        await send({"type": "http.response.body", "body": b"Halo needs the access password."})

    def _authorized(self, scope) -> bool:
        header = dict(scope["headers"]).get(b"authorization", b"")
        scheme, _, value = header.partition(b" ")
        if scheme.lower() != b"basic":
            return False
        try:
            _, _, password = base64.b64decode(value, validate=True).partition(b":")
        except (binascii.Error, ValueError):
            return False
        return secrets.compare_digest(password, self.password)
