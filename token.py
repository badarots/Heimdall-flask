from itsdangerous import URLSafeTimedSerializer

SECRET_KEY = 'babaca_muleque'
SALT = 'tunemimagina'


def generate_token(email):
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    return serializer.dumps(email, salt=SALT)


def confirm_token(token, expiration=3600):
    serializer = URLSafeTimedSerializer(SECRET_KEY)
    try:
        email = serializer.loads(
            token,
            salt=SALT,
            max_age=expiration
        )
    except:
        return False
    return email
