# Tax System module for AllianceAuth.<a name="aa-taxsystem"></a>

![Release](https://img.shields.io/pypi/v/aa-taxsystem?label=release)
![Licence](https://img.shields.io/github/license/geuthur/aa-taxsystem)
![Python](https://img.shields.io/pypi/pyversions/aa-taxsystem)
![Django](https://img.shields.io/pypi/frameworkversions/django/aa-taxsystem.svg?label=django)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/Geuthur/aa-taxsystem/master.svg)](https://results.pre-commit.ci/latest/github/Geuthur/aa-taxsystem/master)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Tests](https://github.com/Geuthur/aa-taxsystem/actions/workflows/autotester.yml/badge.svg)](https://github.com/Geuthur/aa-taxsystem/actions/workflows/autotester.yml)
[![codecov](https://codecov.io/gh/Geuthur/aa-taxsystem/graph/badge.svg?token=IGpkrAuv42)](https://codecov.io/gh/Geuthur/aa-taxsystem)
[![Translation status](https://weblate.geuthur.de/widget/allianceauth/aa-memberaudit-doctrine-checker/svg-badge.svg)](https://weblate.geuthur.de/engage/allianceauth/)
[![Discord](https://img.shields.io/discord/337275567487320064?label=discord)](https://discord.gg/WrHzA4rnxA)

[![ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/W7W810Q5J4)

A Tax System for Corporation to Monitor Payments like Renting Tax, etc.

______________________________________________________________________

- [AA Tax System](#aa-taxsystem)
  - [Features](#features)
  - [Upcoming](#upcoming)
  - [Screenshots](#screenshots)
  - [Installation](#features)
    - [Step 1 - Install the Package](#step1)
    - [Step 2 - Configure Alliance Auth](#step2)
    - [Step 3 - Add the Scheduled Tasks and Settings](#step3)
    - [Step 4 - Migration to AA](#step4)
    - [Step 5 - Setting up Permissions](#step5)
    - [Step 6 - (Optional) Setting up Compatibilies](#step6)
  - [Documentation](#documentation)
  - [Translations](#translations)
  - [Contributing](#contributing)

## Features<a name="features"></a>

- **Multi-Owner Support**: Manage both Corporations and Alliances
- **Corporation & Alliance Tax System**
  - Statistics
    - Owner Information
    - Payments
    - Tax Accounts
    - Division Information
    - Update Status
  - Member Tracking
    - Check Member is registered in Auth
    - Check Member is Alt Char
    - Report members as missing if they leave the corporation/alliance
  - Payment System
    - Allocate User from Member Tracking
    - Automatic Payment Tracking
    - Automatic Payment Approval via Filters
    - Filtering Amount, Reason, Date
  - Payments
    - Track Payments that meets filters
    - Manual approval workflow for unfiltered payments
  - Log System
    - Logs Actions from Administration Section
    - Payment history tracking

## Upcoming<a name="upcoming"></a>

- Notify via Discord
- Data export functionality

## Screenshots<a name="screenshots"></a>

### Administration View

![Screenshot](https://raw.githubusercontent.com/Geuthur/aa-taxsystem/refs/heads/master/docs/images/administration.png)

### Account User Payments History

![Screenshot](https://raw.githubusercontent.com/Geuthur/aa-taxsystem/refs/heads/master/docs/images/administrationpaymentaccount.png)

### Tax Filters

![Screenshot](https://raw.githubusercontent.com/Geuthur/aa-taxsystem/refs/heads/master/docs/images/filters.png)

### Payments Details

![Screenshot](https://raw.githubusercontent.com/Geuthur/aa-taxsystem/refs/heads/master/docs/images/paymentdetails.png)

### Payments

![Screenshot](https://raw.githubusercontent.com/Geuthur/aa-taxsystem/refs/heads/master/docs/images/payments.png)

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

- Add `'taxsystem',` to `INSTALLED_APPS`

### Step 3 - Add the Scheduled Tasks<a name="step3"></a>

To set up the Scheduled Tasks add following code to your `local.py`

```python
CELERYBEAT_SCHEDULE["taxsystem_update_all_taxsytem"] = {
    "task": "taxsystem.tasks.update_all_taxsytem",
    "schedule": 1800,
}
```

### Step 3.1 - (Optional) Add own Logger File

To set up the Logger add following code to your `local.py`
Ensure that you have writing permission in logs folder.

```python
LOGGING["handlers"]["taxsystem_file"] = {
    "level": "INFO",
    "class": "logging.handlers.RotatingFileHandler",
    "filename": os.path.join(BASE_DIR, "log/taxsystem.log"),
    "formatter": "verbose",
    "maxBytes": 1024 * 1024 * 5,
    "backupCount": 5,
}
LOGGING["loggers"]["extensions.taxsystem"] = {
    "handlers": ["taxsystem_file", "console", "extension_file"],
    "level": "DEBUG",
}
```

### Step 4 - Migration to AA<a name="step4"></a>

```shell
python manage.py collectstatic
python manage.py migrate
```

### Step 5 - Setting up Permissions<a name="step5"></a>

With the Following IDs you can set up the permissions for the Tax System

| ID                    | Description                      |                                                                |
| :-------------------- | :------------------------------- | :------------------------------------------------------------- |
| `basic_access`        | Can access the Tax System module | All Members with the Permission can access the Tax System.     |
| `create_access`       | Can add Corporation/Alliance     | Users with this permission can add corporations and alliances. |
| `manage_own_corp`     | Can manage own Corporation       | Users with this permission can manage own corporation.         |
| `manage_corps`        | Can manage all Corporations      | Users with this permission can manage all corporations.        |
| `manage_own_alliance` | Can manage own Alliance          | Users with this permission can manage own alliance.            |
| `manage_alliances`    | Can manage all Alliances         | Users with this permission can manage all alliances.           |

### Step 6 - (Optional) Setting up Compatibilies<a name="step6"></a>

The Following Settings can be setting up in the `local.py`

- TAXSYSTEM_APP_NAME: `"YOURNAME"` - Set the name of the APP

- TAXSYSTEM_BULK_BATCH_SIZE: `500` - Maximum database batch size per operation. Reduce (e.g., 250) if encountering 'max_allowed_packet' errors, increase for better performance if MySQL is configured with higher limits
  Advanced Settings: Stale Status for Each Section

- TAXSYSTEM_STALE_TYPES = `{ "wallet": 60, "divisions": 60, "division_names": 60, "members": 60, "payments": 60, "tax_accounts":60, "deadlines": 1440 }` - Defines the stale status duration (in minutes) for each section.

## Documentation<a name="documentation"></a>

For detailed information on how to use the Tax System, please refer to our comprehensive [User Manual](https://github.com/Geuthur/aa-taxsystem/blob/master/docs/USER_MANUAL.md).

The manual covers:

- Getting started with the Tax System
- Adding Corporations and Alliances
- Payment System functionality
- Filter configuration
- Account management
- Administration features
- FAQ and troubleshooting

## Translations<a name="translations"></a>

[![Translations](https://weblate.geuthur.de/widget/allianceauth/aa-taxsystem/multi-auto.svg)](https://weblate.geuthur.de/engage/allianceauth/)

Help us translate this app into your language or improve existing translations. Join our team!"

## Contributing <a name="contributing"></a>

You want to improve the project?
Please ensure you read the [contribution guidelines](https://github.com/Geuthur/aa-taxsystem/blob/master/CONTRIBUTING.md)
