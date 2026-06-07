from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'django-insecure-dev-key-change-in-production')
DEBUG = os.getenv('DJANGO_DEBUG', 'True').lower() in ('true', '1', 'yes')
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', '127.0.0.1,localhost').split(',')

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',

    'storages',
    'ckeditor',
    'ckeditor_uploader',
    'main',
    'music',
    'accounts',
    'cart',
    'blog',
]

AUTH_USER_MODEL = 'accounts.User'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.locale.LocaleMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'main.context_processors.site_settings',
                'main.context_processors.ad_modal',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': os.getenv('DB_ENGINE', 'django.db.backends.mysql'),
        'NAME': os.getenv('DB_NAME', 'onritm2_db'),
        'USER': os.getenv('DB_USER', 'root'),
        'PASSWORD': os.getenv('DB_PASSWORD', ''),
        'HOST': os.getenv('DB_HOST', '127.0.0.1'),
        'PORT': os.getenv('DB_PORT', '3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
]

LANGUAGE_CODE = 'fa-ir'
TIME_ZONE = 'Asia/Tehran'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATICFILES_DIRS = [
    BASE_DIR / 'assets',
    BASE_DIR / 'dist',
    BASE_DIR / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

SMS_IR_API_KEY = os.getenv('SMS_IR_API_KEY', '')
SMS_IR_TEMPLATE_ID = os.getenv('SMS_IR_TEMPLATE_ID', '')

ZARINPAL_MERCHANT_ID = os.getenv('ZARINPAL_MERCHANT_ID', '')
ZARINPAL_SANDBOX = os.getenv('ZARINPAL_SANDBOX', 'True').lower() in ('true', '1', 'yes')
ZARINPAL_REQUEST_URL = os.getenv('REQUEST_URL', '')
ZARINPAL_VERIFY_URL = os.getenv('VERIFY_URL', '')
ZARINPAL_STARTPAY_URL = os.getenv('STARTPAY_URL', '')
OTP_EXPIRE_MINUTES = 5

ARVAN_S3_ENDPOINT = os.getenv('ARVAN_S3_ENDPOINT', 'https://s3.ir-thr-at1.arvanstorage.com')
ARVAN_S3_ACCESS_KEY = os.getenv('ARVAN_S3_ACCESS_KEY', '')
ARVAN_S3_SECRET_KEY = os.getenv('ARVAN_S3_SECRET_KEY', '')
ARVAN_S3_BUCKET = os.getenv('ARVAN_S3_BUCKET', '')
ARVAN_S3_PUBLIC_URL = os.getenv('ARVAN_S3_PUBLIC_URL', '')

if ARVAN_S3_BUCKET:
    STORAGES = {
        'default': {
            'BACKEND': 'main.storage.HybridS3Storage',
            'OPTIONS': {
                'access_key': ARVAN_S3_ACCESS_KEY,
                'secret_key': ARVAN_S3_SECRET_KEY,
                'bucket_name': ARVAN_S3_BUCKET,
                'endpoint_url': ARVAN_S3_ENDPOINT,
                'custom_domain': ARVAN_S3_PUBLIC_URL.replace('https://', '').replace('http://', '') if ARVAN_S3_PUBLIC_URL else None,
                'default_acl': 'public-read',
                'querystring_auth': False,
                'file_overwrite': False,
            },
        },
        'staticfiles': {
            'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
        },
    }

CKEDITOR_CONFIGS = {
    'default': {
        'toolbar': 'full',
        'height': 300,
        'width': '100%',
        'language': 'fa',
        'filebrowserUploadUrl': '/ckeditor/upload/',
        'filebrowserBrowseUrl': '/ckeditor/browse/',
    },
}
CKEDITOR_UPLOAD_PATH = 'uploads/'
