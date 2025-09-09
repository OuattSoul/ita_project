import jwt
from django.conf import settings

decoded = jwt.decode("<ACCESS_TOKEN>", settings.SECRET_KEY, algorithms=["HS256"])
print(decoded["exp"])  # timestamp d’expiration
