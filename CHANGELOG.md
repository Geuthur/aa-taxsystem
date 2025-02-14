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
- Shake Animation
- API
  - Payment System
    - Account Payments Overview
  - Character
    - Payment Details
- Log System
  - Logs Payment changes
- Views
  - Logs for each Payment Change
- Lazy Functions
  - Add Icon Generate function
- Tasks
  - Logs fo Payments

### Changed

- Modal System
- Tax Model
  - States Choice to Status
  - `payment_pool` to `deposit`
- Payments
  - States to Status
  - Approval to RequestStatus
  - `payment_user` to `account`
  - `payment_status` to `status`
  - `system` to `reviser`
  - Removed payment_date
  - Removed approver_text
- Button System
  - Add Ajax Support for Modal System
- Payments View
  - Removed `request_status`, `reviser`, `reason` row

### Fixed

- Wrong Bool State on `has_paid` property if `payment_pool` is negative [#2](https://github.com/Geuthur/aa-taxsystem/issues/2)
- Locale Folder has wrong `__init__`
- Modal System Error Handler
- Error if User has no Main Character defined yet

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
