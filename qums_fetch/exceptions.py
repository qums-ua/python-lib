class Error(Exception):
    """Base exception for all client errors."""


class LoginPageParseError(Error):
    """The login page's HTML didn't contain what we expected (token or
    captcha image). Usually means the site's markup changed."""


class LoginFailedError(Error):
    """The login POST didn't land on the student menu, for a reason we
    couldn't attribute to a specific field. Prefer CaptchaError or
    CredentialsError below when the page tells us which — this is the
    fallback for anything else (ERP-side error, unexpected markup)."""


class CaptchaError(LoginFailedError):
    """The captcha reading was wrong (page showed a
    'field-validation-error' element). Retry with a fresh captcha —
    this tells you nothing about whether the credentials were correct,
    since the ERP validates captcha before it ever checks credentials
    and won't report a credentials error while captcha is wrong."""


class CredentialsError(LoginFailedError):
    """Username/password were rejected (page showed a
    'validation-summary-errors' element) while the captcha itself was
    accepted. Retrying with a new captcha won't help — the credentials
    need to change."""
