# Changelog

## [0.5.1] - IN DEVELOPMENT

### Added

- Approver text field for `payments` model
- Undo Payments Url
- Tax System Standard CSS
- Form Generation System
- Inactive Button for Payment System Users
- Datatable Filters for Payments, Payment System, Members
- Division Overview in Administration Section
- Miscellaneous Statistics in Administration Section
- Corporation Name in Payments View
- Reason row into Payments
- Log System for Administration Actions

### Fixed

- Wrong Bool State on `has_paid` property if `payment_pool` is negative [#2](https://github.com/Geuthur/aa-taxsystem/issues/2)
- Locale Folder has wrong `__init__`

## [0.5.0.3] - 2025-02-10

### Hot Fix

- Manage Permissions for Corporations

### Remove

- Standard Permissions for Filters

## [0.5.0] - 2025-02-09

> [!NOTE]
> If you were using version 0.0.1, you must reinstall the entire tax system as the migrations have been changed.

### Added

- API System
  - Administration
  - Dashboard
  - Payments
  - Payment System
- Filter System with Hook Feature
  - Amount Filter
  - Reason Filter
  - Date Filter
- Corporation Overview
  - Members Tracking
  - Payment Users
- Payments
  - Automatic Payments Approves via Filter
  - Manual Approvment
- Models
  - OwnerAudit
  - Members
  - Payment System
  - Payments
  - WalletJournal
- Translation
  - German
  - English
- Tasks
  - Wallet Journal Task
  - Members Tracking Task
  - Payments Task
  - Payment System Task
- Modal
  - Modal System
  - Approve Modal
  - Confirm Modal
  - Table Modal

## [0.0.1] - 2025-02-06

### Added

- Initial public release
