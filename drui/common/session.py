"""
Encrypted Flask session handling using Fernet symmetric encryption.

This module provides a drop-in replacement for Flask's default signed-cookie
session mechanism. Instead of signing session data, it encrypts the entire
payload with the Fernet (AES-128-CBC + HMAC-SHA256) scheme, ensuring both
confidentiality and integrity of the session contents.
"""

import json
import typing as t
from base64 import urlsafe_b64encode
from hashlib import sha256

import flask
from cryptography.fernet import Fernet
from flask.sessions import SecureCookieSession
from flask.sessions import SecureCookieSessionInterface

from drui.common.logging import get_logger

log = get_logger(__name__)


class SessionDecryptionError(Exception):
    """
    Raised when session decryption fails due to an invalid or tampered token.
    """


class FernetSessionSerializer:
    """
    Serialize session data to/from encrypted Fernet tokens.
    """

    def __init__(self, fernet: Fernet) -> None:
        """
        Initialize the serializer with a Fernet instance.

        :param fernet: a :class:`cryptography.fernet.Fernet` instance
        """
        self.fernet: Fernet = fernet

    def dumps(self, value: t.Dict[str, t.Any]) -> str:
        """
        Serialize and encrypt a session dictionary.

        :param value: a JSON-serializable dictionary representing the session data
        :return: the encrypted session token
        """
        payload = json.dumps(value).encode('utf-8')
        encrypted = self.fernet.encrypt(payload)
        return encrypted.decode('utf-8')

    def loads(self, value: str, max_age: t.Optional[int] = None) -> t.Dict[str, t.Any]:
        """
        Decrypt and deserialize a session token.

        :param value: the encrypted session token
        :param max_age: (optional) the maximum age of the token (in seconds)
        :return: the original session dictionary
        :raises SessionDecryptionError: if the token is invalid or tampered with
        """
        try:
            encrypted = value.encode('utf-8')
            decrypted = self.fernet.decrypt(encrypted, ttl=max_age)
            return json.loads(decrypted.decode('utf-8'))
        except Exception as error:
            log.error(f'Failed to deserialize session: {error}')
            raise SessionDecryptionError() from error


class EncryptedSessionInterface(SecureCookieSessionInterface):
    """
    A Flask session interface backed by Fernet-encrypted cookies.
    """

    def get_signing_serializer(self, app: flask.Flask) -> t.Optional[FernetSessionSerializer]:
        """
        Build a Fernet-based serializer for the given Flask application.

        Fernet requires a 32-byte key. We hash the Flask secret_key to generate it.

        :param app: the application instance
        :return: a FernetSessionSerializer instance or None
        """
        if not app.secret_key:
            return None

        secret = app.secret_key
        if isinstance(secret, str):
            secret = secret.encode('utf-8')

        key_hash = sha256(secret).digest()
        fernet_key = urlsafe_b64encode(key_hash)

        fernet = Fernet(fernet_key)
        return FernetSessionSerializer(fernet)

    def open_session(self, app: flask.Flask, request: flask.Request) -> t.Optional[SecureCookieSession]:
        """
        Open and decrypt a session from the request cookie.

        :param app: the application instance
        :param request: the incoming request
        :return: a session object or None
        """
        serializer = self.get_signing_serializer(app)
        if serializer is None:
            return None

        name = self.get_cookie_name(app)
        cookie_value = request.cookies.get(name)
        if not cookie_value:
            return self.session_class()

        max_age = int(app.permanent_session_lifetime.total_seconds())

        try:
            data = serializer.loads(cookie_value, max_age=max_age)
            return self.session_class(data)
        except SessionDecryptionError:
            log.warning(f'Clearing corrupted session cookie for {request.remote_addr}')
            session = self.session_class()
            session.modified = True
            return session
