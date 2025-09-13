"""Django settings for core project."""

from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
# Load from environment variable
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', 'django-insecure-g7ccbck23uiam(r(*0-&^57v#94(2^kt#buh!mn$fbq)l8+=$$')

# --- PRODUCTION SETTINGS ---
# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
ALLOWED_HOSTS = ['btrees.in', 'admin.btrees.in']
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')


# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',
    'accounts',
    'studentsdb',
    'placementdrive',
    'placementdb',
    'batchdb',
    'trainersdb',
    'consultantdb',
    'settingsdb',
    'paymentdb',
    'coursedb',
    'django_select2',
    'core',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'settingsdb.middleware.CaptureUserMiddleware',
    'accounts.middleware.RolePermissionsMiddleware',
    'accounts.middleware.RoleBasedRedirectMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'core.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')],
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

WSGI_APPLICATION = 'core.wsgi.application'


# Database configuration from environment variables
DATABASES = {
    'default': {
        'ENGINE': os.environ.get('DB_ENGINE', 'django.db.backends.postgresql'),
        'NAME': os.environ.get('DB_NAME', 'btree_db'),
        'USER': os.environ.get('DB_USER', 'btree_user'),
        'PASSWORD': os.environ.get('DB_PASSWORD', 'BTree@2025'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}



# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True


# --- STATIC FILES CONFIGURATION ---
# The URL to use when referring to static files located in STATIC_ROOT.
STATIC_URL = 'static/'


# A list of directories where Django will look for your project's source static files.
# STATICFILES_DIRS = [
#     os.path.join(BASE_DIR, 'static'),
# ]


# --- MEDIA FILES CONFIGURATION (User-uploaded content) ---
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# --- AUTHENTICATION SETTINGS ---
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'accounts.CustomUser'
LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'home'
LOGOUT_REDIRECT_URL = 'login'

# Email Configuration from environment variables
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True').lower() == 'true'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'btreesystem@gmail.com')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', 'xaiqetsigdskrwqn')
DEFAULT_FROM_EMAIL = os.environ.get('EMAIL_HOST_USER', 'btreesystem@gmail.com')

# for developement
# DEBUG = True
# ALLOWED_HOSTS = ['*']

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }