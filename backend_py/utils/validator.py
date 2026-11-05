from email_validator import EmailNotValidError, validate_email

from utils.common import js_typeof


def _assert_string(v):
    if not isinstance(v, str):
        raise TypeError(f"Expected a string but received a {js_typeof(v)}")


def _is_email(v) -> bool:
    _assert_string(v)
    try:
        validate_email(v, check_deliverability=False)
        return True
    except EmailNotValidError:
        return False


def _is_length(v, min_len=0, max_len=None) -> bool:
    _assert_string(v)
    n = len(v)
    return n >= min_len and (max_len is None or n <= max_len)


def validate(email, password):
    # ---------- Required ----------
    if not email or not password:
        raise Exception("Email and Password required")

    # ---------- Email Validation ----------
    if not _is_email(email):
        raise Exception("Invalid Email")

    if not _is_length(email, 4, 100):
        raise Exception("Email length invalid")

    # ---------- Password Validation ----------
    # validator.isStrongPassword with minLength 4 and every other minimum = 0
    _assert_string(password)
    if not len(password) >= 4:
        raise Exception("Password must be 4-128 chars with upper, lower, number & symbol")

    if not _is_length(password, 0, 128):
        raise Exception("Password too long")

    if " " in password:
        raise Exception("Password cannot contain spaces")
