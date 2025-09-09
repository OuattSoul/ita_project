from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models

class CustomUserManager(BaseUserManager):
    def create_user(self, fname, password=None, **extra_fields):
        if not fname:
            raise ValueError("Le prénom est obligatoire")
        user = self.model(fname=fname, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, fname, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        return self.create_user(fname, password, **extra_fields)



class CustomUser(AbstractBaseUser, PermissionsMixin):
    fname = models.CharField(max_length=150, unique=True)
    lname = models.EmailField(unique=True)
    #is_active = models.BooleanField(default=True)
    #is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = "fname"   # login avec user_name
    REQUIRED_FIELDS = ["password"]

    class Meta:
        db_table = "employees"   # ✅ nom physique en DB Postgres



"""class CustomUser(AbstractBaseUser, PermissionsMixin):
    fname = models.CharField(max_length=150, unique=True)
    last_name = models.CharField(max_length=150, blank=True)
    role = models.CharField(max_length=20, default='worker')
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = "fname"     # login avec fname
    REQUIRED_FIELDS = ["last_name"]

    def __str__(self):
        return f"{self.fname} {self.last_name}"""



