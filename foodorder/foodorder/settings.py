from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-48rjmo@lnkvv+_w%w1bww165oiu%@%+=+rejw5*@#*td4%=8x*'

DEBUG = False

ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'api',
    "corsheaders",
    'rest_framework',
    'storages',  # ADD THIS
]

CORS_ALLOW_ALL_ORIGINS = True

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'foodorder.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'foodorder.wsgi.application'

if os.getenv("RENDER"):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': 'django_db_hvuc',
            'USER': 'django_db_hvuc_user',
            'PASSWORD': 'xgrVD94i95Qq3FtgpyHCie2QYJVb2hwp',
            'HOST': 'dpg-d737bc7fte5s73est2b0-a.singapore-postgres.render.com',
            'PORT': '5432',
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Supabase S3 Storage
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

AWS_ACCESS_KEY_ID = os.getenv('49bab0d9804d8c88fb15c373924351cd')
AWS_SECRET_ACCESS_KEY = os.getenv('df9b8c8a6d8f12c3638e4485083e09ad8a8d01e519f3a0f4c32cf9bef5ae7007')
AWS_STORAGE_BUCKET_NAME = 'media'
AWS_S3_ENDPOINT_URL = 'https://eynolkwnzoheaxkezbbs.storage.supabase.co/storage/v1/s3'
AWS_S3_REGION_NAME = 'ap-northeast-1'
AWS_DEFAULT_ACL = 'public-read'
AWS_QUERYSTRING_AUTH = False

MEDIA_URL = 'https://eynolkwnzoheaxkezbbs.supabase.co/storage/v1/object/public/media/'