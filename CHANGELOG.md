# Changelog

## [0.5.5] - IN DEVELOPMENT

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
