"""
DO NOT EDIT THIS FILE

This settings file contains everything needed for Alliance Auth projects to function.
It gets overwritten by the 'allianceauth update' command.
If you wish to make changes, overload the setting in your project's settings file (local.py).
"""

# Standard Library
import os

# Third Party
from celery.schedules import crontab

# Django
from django.contrib import messages
from django.utils.translation import gettext_lazy as _

INSTALLED_APPS = [
    "allianceauth",  # needs to be on top of this list to support favicons in Django admin (see https://gitlab.com/allianceauth/allianceauth/-/issues/1301)
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.humanize",
    "django_celery_beat",
    "solo",
    "bootstrapform",
    "django_bootstrap5",  # https://github.com/zostera/django-bootstrap5
    "sortedm2m",
    "esi",
    "allianceauth.framework",
    "allianceauth.authentication",
    "allianceauth.services",
    "allianceauth.eveonline",
    "allianceauth.groupmanagement",
    "allianceauth.notifications",
    "allianceauth.thirdparty.navhelper",
    "allianceauth.analytics",
    "allianceauth.menu",
    "allianceauth.theme",
    "allianceauth.theme.darkly",
    "allianceauth.theme.flatly",
    "allianceauth.theme.materia",
    "allianceauth.custom_css",
    "allianceauth.crontab",
    "sri",
]

SRI_ALGORITHM = "sha512"
SECRET_KEY = "wow I'm a really bad default secret key"

# Celery configuration
BROKER_URL = "redis://localhost:6379/0"
CELERYBEAT_SCHEDULER = "allianceauth.crontab.schedulers.OffsetDatabaseScheduler"
CELERYBEAT_SCHEDULE = {
    "esi_cleanup_callbackredirect": {
        "task": "esi.tasks.cleanup_callbackredirect",
        "schedule": crontab(minute="0", hour="*/4"),
    },
    "esi_cleanup_token": {
        "task": "esi.tasks.cleanup_token",
        "schedule": crontab(minute="0", hour="0"),
    },
    "run_model_update": {
        "task": "allianceauth.eveonline.tasks.run_model_update",
        "schedule": crontab(minute="0", hour="*/6"),
        "apply_offset": True,
    },
    "check_all_character_ownership": {
        "task": "allianceauth.authentication.tasks.check_all_character_ownership",
        "schedule": crontab(minute="0", hour="*/4"),
        "apply_offset": True,
    },
    "analytics_daily_stats": {
        "task": "allianceauth.analytics.tasks.analytics_daily_stats",
        "schedule": crontab(minute="0", hour="2"),
    },
}


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.dirname(PROJECT_DIR)

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "allianceauth.authentication.middleware.UserSettingsMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "allianceauth.urls"

LOCALE_PATHS = (os.path.join(BASE_DIR, "locale/"),)

LANGUAGES = (  # Sorted by Language Code alphabetical order + English at top
    ("en", _("English")),
    # ("cs-cz", _("Czech")), #Not yet at 50% translated
    ("de", _("German")),
    ("es", _("Spanish")),
    ("it-it", _("Italian")),
    ("ja", _("Japanese")),
    ("ko-kr", _("Korean")),
    ("fr-fr", _("French")),
    ("nl-nl", _("Dutch")),
    ("pl-pl", _("Polish")),
    ("ru", _("Russian")),
    ("uk", _("Ukrainian")),
    ("zh-hans", _("Simplified Chinese")),
)

# Django's language codes are different from some of the libraries we use,
# so we need to map them.
LANGUAGE_MAPPING = {
    "DataTables": {
        "cs-cz": "cs",
        "de": "de-DE",
        "es": "es-ES",
        "fr-fr": "fr-FR",
        "it-it": "it-IT",
        "ja": "ja",
        "ko-kr": "ko",
        "nl-nl": "nl-NL",
        "pl-pl": "pl",
        "ru": "ru",
        "uk": "uk",
        "zh-hans": "zh-HANT",
    },
    "MomentJS": {
        "cs-cz": "cs",
        "de": "de",
        "es": "es",
        "fr-fr": "fr",
        "it-it": "it",
        "ja": "ja",
        "ko-kr": "ko",
        "nl-nl": "nl",
        "pl-pl": "pl",
        "ru": "ru",
        "uk": "uk",
        "zh-hans": "zh-cn",
    },
}

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(PROJECT_DIR, "templates")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",
                "django.template.context_processors.media",
                "django.template.context_processors.static",
                "django.template.context_processors.tz",
                "allianceauth.context_processors.auth_settings",
            ],
        },
    },
]

WSGI_APPLICATION = "allianceauth.wsgi.application"

# Password validation
# https://docs.djangoproject.com/en/1.10/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

AUTHENTICATION_BACKENDS = [
    "allianceauth.authentication.backends.StateBackend",
    "django.contrib.auth.backends.ModelBackend",
]

# Internationalization
# https://docs.djangoproject.com/en/1.10/topics/i18n/

LANGUAGE_CODE = "en-us"

LANGUAGE_COOKIE_AGE = 1209600

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.10/howto/static-files/
STATIC_URL = "/static/"
STATICFILES_DIRS = [
    os.path.join(PROJECT_DIR, "static"),
]
STATIC_ROOT = os.path.join(BASE_DIR, "static")

# Bootstrap messaging css workaround
MESSAGE_TAGS = {messages.ERROR: "danger error"}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",  # change the 1 here for the DB used
    }
}

SESSION_ENGINE = "django.contrib.sessions.backends.cached_db"

DEBUG = True
ALLOWED_HOSTS = ["*"]
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": str(os.path.join(BASE_DIR, "alliance_auth.sqlite3")),
    },
}

SITE_NAME = "Alliance Auth"

DEFAULT_THEME = "allianceauth.theme.flatly.auth_hooks.FlatlyThemeHook"
DEFAULT_THEME_DARK = "allianceauth.theme.darkly.auth_hooks.DarklyThemeHook"  # Legacy AAv3 user.profile.night_mode=1

LOGIN_URL = "auth_login_user"  # view that handles login logic

LOGIN_REDIRECT_URL = "authentication:dashboard"  # default destination when logging in if no redirect specified
LOGOUT_REDIRECT_URL = "authentication:dashboard"  # destination after logging out
# Both of these redirects accept values as per the django redirect shortcut
# https://docs.djangoproject.com/en/1.11/topics/http/shortcuts/#redirect
# - url names eg 'authentication:dashboard'
# - relative urls eg '/dashboard'
# - absolute urls eg 'http://example.com/dashboard'

# scopes required on new tokens when logging in. Cannot be blank.
LOGIN_TOKEN_SCOPES = ["publicData"]

EMAIL_TIMEOUT = 15

# number of days email verification links are valid for
ACCOUNT_ACTIVATION_DAYS = 1

ESI_API_URL = "https://esi.evetech.net/"

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s",
            "datefmt": "%d/%b/%Y %H:%M:%S",
        },
        "simple": {"format": "%(levelname)s %(message)s"},
    },
    "handlers": {
        "log_file": {
            "level": "INFO",  # edit this line to change logging level to file
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(BASE_DIR, "log/allianceauth.log"),
            "formatter": "verbose",
            "maxBytes": 1024 * 1024 * 5,  # edit this line to change max log file size
            "backupCount": 5,  # edit this line to change number of log backups
        },
        "extension_file": {
            "level": "ERROR",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(BASE_DIR, "log/extensions.log"),
            "formatter": "verbose",
            "maxBytes": 1024 * 1024 * 5,  # edit this line to change max log file size
            "backupCount": 5,  # edit this line to change number of log backups
        },
        "console": {
            "level": "DEBUG",  # edit this line to change logging level to console
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "notifications": {  # creates notifications for users with logging_notifications permission
            "level": "ERROR",  # edit this line to change logging level to notifications
            "class": "allianceauth.notifications.handlers.NotificationHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "allianceauth": {
            "handlers": ["log_file", "console", "notifications"],
            "level": "DEBUG",
        },
        "extensions": {
            "handlers": ["extension_file", "console"],
            "level": "ERROR",
        },
        "django": {
            "handlers": ["log_file", "console"],
            "level": "ERROR",
        },
        "esi": {
            "handlers": ["log_file", "console"],
            "level": "ERROR",
        },
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
