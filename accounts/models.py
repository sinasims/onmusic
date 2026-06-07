from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    def create_user(self, phone, password=None, **extra_fields):
        if not phone:
            raise ValueError('شماره موبایل الزامی است')
        user = self.model(phone=phone, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, phone, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(phone, password, **extra_fields)


class User(AbstractUser):
    phone = models.CharField('شماره موبایل', max_length=11, unique=True)
    is_verified = models.BooleanField('تایید شده', default=False)
    phone_verified = models.BooleanField('شماره تایید شده', default=False)

    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        blank=True,
        null=True,
    )

    objects = UserManager()

    USERNAME_FIELD = 'phone'
    REQUIRED_FIELDS = []

    email = models.EmailField(_('email address'), blank=True, null=True)

    class Meta:
        verbose_name = 'کاربر'
        verbose_name_plural = 'کاربران'

    def __str__(self):
        return self.phone or self.email or f'User {self.id}'


class OTPCode(models.Model):
    phone = models.CharField('شماره موبایل', max_length=11)
    code = models.CharField('کد', max_length=6)
    created_at = models.DateTimeField('ایجاد شده', auto_now_add=True)
    is_used = models.BooleanField('استفاده شده', default=False)

    class Meta:
        verbose_name = 'کد تایید'
        verbose_name_plural = 'کدهای تایید'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.phone} - {self.code}'
