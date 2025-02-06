# Tax System module for AllianceAuth.<a name="aa-taxsystem"></a>

A Tax System for Corporation to Monitor Payments like Renting Tax, etc.

______________________________________________________________________

- [AA Tax System](#aa-taxsystem)
  - [Features](#features)
  - [Upcoming](#upcoming)
  - [Installation](#features)
    - [Step 1 - Install the Package](#step1)
    - [Step 2 - Configure Alliance Auth](#step2)
    - [Step 3 - Add the Scheduled Tasks and Settings](#step3)
    - [Step 4 - Migration to AA](#step4)
    - [Step 5 - Setting up Permissions](#step5)
    - [Step 6 - (Optional) Setting up Compatibilies](#step6)
  - [Highlights](#highlights)

## Features<a name="features"></a>

## Upcoming<a name="upcoming"></a>

## Installation<a name="installation"></a>

> [!NOTE]
> AA Tax System needs at least Alliance Auth v4.6.0
> Please make sure to update your Alliance Auth before you install this APP

### Step 1 - Install the Package<a name="step1"></a>

Make sure you're in your virtual environment (venv) of your Alliance Auth then install the pakage.

```shell
pip install aa-taxsystem
```

### Step 2 - Configure Alliance Auth<a name="step2"></a>

Configure your Alliance Auth settings (`local.py`) as follows:

- Add `'allianceauth.corputils',` to `INSTALLED_APPS`
- Add `'eveuniverse',` to `INSTALLED_APPS`
- Add `'taxsystem',` to `INSTALLED_APPS`

### Step 3 - Add the Scheduled Tasks<a name="step3"></a>

To set up the Scheduled Tasks add following code to your `local.py`

```python
CELERYBEAT_SCHEDULE["taxsystem_update_all_corps"] = {
    "task": "taxsystem.tasks.update_all_corps",
    "schedule": crontab(minute=0, hour="*/1"),
}
```

### Step 4 - Migration to AA<a name="step4"></a>

```shell
python manage.py collectstatic
python manage.py migrate
```

### Step 5 - Setting up Permissions<a name="step5"></a>

With the Following IDs you can set up the permissions for the Tax System

| ID                 | Description                      |                                                            |
| :----------------- | :------------------------------- | :--------------------------------------------------------- |
| `basic_access`     | Can access the Tax System module | All Members with the Permission can access the Tax System. |
| `manage_access   ` | Can manage Tax System            | Can modify/remove tax settings.                            |
| `create_access`    | Can add Corporation              | Users with this permission can add corporation.            |

### Step 6 - (Optional) Setting up Compatibilies<a name="step6"></a>

The Following Settings can be setting up in the `local.py`

- TAXSYSTEM_APP_NAME: `"YOURNAME"` - Set the name of the APP

- TAXSYSTEM_LOGGER_USE: `True / False` - Set to use own Logger File

If you set up TAXSYSTEM_LOGGER_USE to `True` you need to add the following code below:

```python
LOGGING_TAXSYSTEM = {
    "handlers": {
        "taxsystem_file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(BASE_DIR, "log/taxsystem.log"),
            "formatter": "verbose",
            "maxBytes": 1024 * 1024 * 5,
            "backupCount": 5,
        },
    },
    "loggers": {
        "taxsystem": {
            "handlers": ["taxsystem_file", "console"],
            "level": "INFO",
        },
    },
}
LOGGING["handlers"].update(LOGGING_TAXSYSTEM["handlers"])
LOGGING["loggers"].update(LOGGING_TAXSYSTEM["loggers"])
```

## Highlights<a name="highlights"></a>

> [!NOTE]
> Contributing
> You want to improve the project?
> Just Make a [Pull Request](https://github.com/Geuthur/aa-taxsystem/pulls) with the Guidelines.
> We Using pre-commit
