# Changelog

## [0.6.2] - 01.08.2025

### Changed

- Removed Payments, Payment System, Own Payments State Save
- Updated German Translation
- Table Sorting for Payments
- Renamed Last Paid to Last Debit
- Use Localisation in Administration Dashboard

## [0.6.2] - 26.07.2025

### Added

- Update Status Sections in Administration Dashboard

### Fixed

- Corporation Wallet Journal not Updating until ETag expire

### Changed

- Moved Update Status Icon to Update Status Dashboard
- `Wallet Activity` Exclude transactions within Corporation

## [0.6.1] - 22.07.2025

### Fixed

- NoneType Error in Administration Dashboard
- Missing Migration

### Removed

- 0006 Migration (created now by `calc_update_needed`)

## [0.6.0] - 11.07.2025

### Fixed

- Wallet Balance not updating correctly
- New Sections not included to Updates
- NoneType Error on Admin Dashboard

### Changed

- Use `Django SRI` for Cache Busting

### Added

- Account View
- FAQ View
- Not Paid Badge in Menu
- Wallet Activity (Last 30 Days)

## [0.5.9] - 11.07.2025

### Added

- dependabot
- `django-esi` dependency

### Changed

- Use `django-esi` new User Agent Guidelines

## [0.5.8] - 05.07.2025

### Changed

- Minimum dependencies
  - allianceauth>=4.8.0

### Fixed

- Missing Static images

## [0.5.7] - 2025-06-17

### Changed

- Divison 1 Name from "" to "Master Wallet"

### Added

- Divison to Payments View & Administration

### Fixed

- `has_paid` property

## [0.5.6] - 2025-05-28

### Added

- Update Section System - Inspired by @\[[Eric Kalkoken](https://gitlab.com/ErikKalkoken/)\]
  - TokenError Handler
  - HTTPInternalServerError, HTTPGatewayTimeoutError Handler
  - Update Section retrieves information between Etag System (Not Updating if NotModified)
  - Disable Update on Token Error
  - Update Information
  - Update Issues Badge
- Admin Menu (superuser only)
- Task System
  - Use Django Manager for Updates
  - Refactor Tasks
- Tests

### Changed

- Use app_utils `LoggerAddTag` Logger System
- Make `README` logger settings optional
- Changed model relation: `corporation` to `owner`
- Renamed payment_system functions args from `user_pk` to `payment_system_pk`
- Optimized url paths in settings
- Added related name for filters model
- Add mariadb 11.4 support
- Model relation from `corporation` to `owner`
- Add Permission req. for update tax views
- Add Python 3.13 support

### Fixed

- `add_corp` bool error

## [0.5.5] - 2025-04-02

### Added

- Timeout Handler for ESI Requests
- Check Payment Accounts
  - Check if Account is in Corporation
  - Update Account on Corporation Change
  - Reactivate Account on returning to Corporation
- `TAXSYSTEM_STALE_TIME` Defines the time (in days) after which data is considered outdated and needs a update
- Member Delete Button
  - Delete Missing Member from Corp Members list

### Changed

- Refactor Task Process
- Update Logger System

### Fixed

- Wrong Payment User Count on Corporation Leave
- Payments Error if no Main Character Exist

## [0.5.4.1] - 2025-02-17

### Hotfix

- Redirect Loop

## [0.5.4] - 2025-02-17

### Added

- Amount, Reason to Payment Details [#10](https://github.com/Geuthur/aa-taxsystem/issues/10)

### Changed

- Moved Templates
- Translations

## [0.5.3] - 2025-02-16

### Fixed

- Permission Issues

### Removed

- `manage_access` permission

## [0.5.2] - 2025-02-16

### Added

- Corporation Menu
- Own Payments View

### Changed

- CSS Style
- Cleaned templates

### Fixed

- Table Error Handler
- Wrong Permission in Administration View

## [0.5.1] - 2025-02-15

### Added

- API System
  - Administration
  - Account Payments Overview
  - Dashboard
  - Payments
  - Payment System
  - Payment Details
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
  - Logs fo Payments
- Modal
  - Modal System
  - Approve Modal
  - Confirm Modal
  - Table Modal
- Logs
  - Log Payment Changes
  - Log Administration Changes

## [0.0.1] - 2025-02-06

### Added

- Initial public release
