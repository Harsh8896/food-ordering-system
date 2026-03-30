from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-change-this'
DEBUG = False
ALLOWED_HOSTS = ['*']

# ======================
# APPS
# ======================
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    'api',
    'corsheaders',
    'rest_framework',
    'storages',
]

# ======================
# MIDDLEWARE
# ======================
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

CORS_ALLOW_ALL_ORIGINS = True

ROOT_URLCONF = 'foodorder.urls'

# ======================
# TEMPLATES
# ======================
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
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

# ======================
# DATABASE
# ======================
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

# ======================
# STATIC
# ======================
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# ======================
# 🔥 SUPABASE S3 (FINAL WORKING)
# ======================

DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

AWS_ACCESS_KEY_ID = os.getenv('SUPABASE_ACCESS_KEY')
AWS_SECRET_ACCESS_KEY = os.getenv('SUPABASE_SECRET_KEY')

AWS_STORAGE_BUCKET_NAME = 'media'

# ✅ CORRECT ENDPOINT
AWS_S3_ENDPOINT_URL = 'https://eynolkwnzoheaxkezbbs.storage.supabase.co'

AWS_S3_SIGNATURE_VERSION = 's3v4'
AWS_DEFAULT_ACL = 'public-read'
AWS_QUERYSTRING_AUTH = False
AWS_S3_FILE_OVERWRITE = False
AWS_S3_ADDRESSING_STYLE = "path"

AWS_S3_USE_SSL = True
AWS_S3_VERIFY = True

MEDIA_URL = 'https://eynolkwnzoheaxkezbbs.supabase.co/storage/v1/object/public/media/'

# ======================
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'