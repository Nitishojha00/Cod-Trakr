import secrets


def generate_otp() -> str:
    # crypto.randomInt(1000, 10000)
    return str(secrets.randbelow(9000) + 1000)
