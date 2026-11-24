class Error(Exception):
    """Base exception for all client errors."""


class LoginPageParseError(Error):
    """The login page did not contain a usable token and captcha image."""


class LoginFailedError(Error):
    """The server rejected the login or the client ran out of attempts."""


class CaptchaError(LoginFailedError):
    """The client could not solve the captcha or the server rejected its answer."""


class CredentialsError(LoginFailedError):
    """The server rejected the username or password."""


class InvalidResponseError(Error):
    """The server returned data in an unexpected format."""


class BlankCaptchaError(Error):
    """The captcha image appeared blank."""
