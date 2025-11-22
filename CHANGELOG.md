# Changelog

## [In Development] - Unreleased

<!--
Section Order:

### Added
### Fixed
### Changed
### Removed
-->

## [2.0.0a3] - 2025-11-22

### Added

- `next_due` property to PaymentAccount and update related views and templates

### Changed

- Generic Views Refactoring
  - `account()` view now supports both Corporation and Alliance owners
  - `faq()` view now supports both Corporation and Alliance owners
  - Views use `get_manage_owner()` for unified owner retrieval
  - Dynamic owner type detection with isinstance() checks
  - Generic Status checks instead of hardcoded CorporationPaymentAccount
  - Backwards compatible context keys maintained
- Humanized Date Display
  - `last_paid` and `next_due` in manage.js now use `moment.fromNow()` for relative time display
  - Account template now uses Django's `naturaltime` filter for all date fields
  - More intuitive date representation (e.g., "2 days ago", "in 5 days")
- View Permission Fix
  - `generic_owner_own_payments()` now correctly uses `get_corporation()` and `get_alliance()` instead of management methods
  - End-user view no longer requires management permissions

## [2.0.0a2] - 2025-11-22

### Fixed

- MultipleObjectsReturned: get() returned more than one AlliancePayments -- it returned 2!

## [2.0.0a1] - 2025-11-22

### Added

- Alliance Tax System
  - Payments
  - Payment Accounts
- Owner Overview Page (`/owners/`)
  - Unified view displaying both Corporations and Alliances
  - Permission-based action buttons (Payments/Manage)
  - DataTables integration with responsive design
  - Portrait display for all owners
  - Active/Inactive status badges
  - Dark theme compatible (btn-warning for manage buttons)
  - Automatic redirect from index to owner overview
- Administration view now checking for permission and if Corporation is still available
- EVE Portrait and Logo Helper Functions
  - Backend lazy helpers: `get_character_portrait_url()`, `get_corporation_logo_url()`, `get_alliance_logo_url()`
  - Template tags: `|character_portrait_url:size`, `|corporation_logo_url:size`, `|alliance_logo_url:size`
- Owner Permissions via Manager Methods
  - `CorporationOwner.objects.manage_to(user)` and `AllianceOwner.objects.manage_to(user)`
  - `visible_to(user)` methods for broader visibility
- Menu navigation now points to Owner Overview instead of payment list

### Fixed

- Test Suite after API parameter migration (158 tests passing, 71% coverage)
  - Updated test parameters from `corporation_id` to `owner_id` for generic owner endpoints
  - Fixed payment creation in character tests to use correct `owner_id` field
  - Fixed response assertions to match new "owner" schema
  - Added missing `MessageMiddleware` to test requests
  - Created missing test data for manage_user tests
  - Fixed FAQ URL routing in access tests
  - Implemented Alliance payment tests with proper factory functions
  - Performance tests now use `assertIsNotNone()` instead of silent skipping
- DataTables warning for empty Owner Overview table (incorrect column count)
- Owner Overview now uses `visible_to()` instead of `manage_to()` for correct permission filtering

### Changed

- Refactor Tax System and prepare for Alliance Tax System migration
- All views are now accessible with or without specifying corporation_id/alliance_id. If not provided, the user's main character's corporation/alliance is used by default.
- Renamed `Manage Tax System` to `Manage Corporation` or `Manage Alliance`
- Index page (`/`) now redirects to Owner Overview instead of payment list
- Owner Overview removes `get_status` column (admin-focused, not user-focused)
- Empty state message changed from "manage" to "view" for better user understanding
- Task Queue Order
- Performance Optimization: N+1 Query Fixes
  - Payment queries now use `select_related()` for account, user, profile, and main_character (70-80% query reduction)
  - Payment System uses `prefetch_related()` for character_ownerships (85-90% query reduction)
  - Members queries optimized with `select_related()` for owner relationships (60-70% faster)
- API Migration: Generic owner endpoints now use `owner_id` parameter instead of `corporation_id`
  - Affects: filter management, payment system, and filter set endpoints
  - Corporation-specific endpoints still use `corporation_id`
- Views Terminology: Permission error messages for generic owner operations now use "owner" instead of "corporation"
- Database Indexes for Performance
- Test Quality: All tests must work properly or fail with clear assertions (no silent skipping allowed)
  - AlliancePayments: Composite index (account, owner_id, request_status, -date) + (request_status, -date)
  - CorporationPayments: Composite index (account, owner_id, request_status, -date) + (request_status, -date)
  - Members: Indexes on (owner, character_name) + (status)
  - Expected: 50%+ faster filtered queries, combined with N+1 fixes: 60-80% total improvement
- Statistics Query Optimization
  - Analyzed and confirmed all statistics functions already use optimal single aggregate() queries
  - `get_payments_statistics()`: 1 query for all counts (total, pending, automatic, manual)
  - `get_payment_system_statistics()`: 1 query for all counts (users, active, inactive, deactivated, paid, unpaid)
  - `get_members_statistics()`: 1 query for all counts (total, mains, alts, unregistered)
  - Dashboard statistics: 3 optimized queries (1 per table) vs potentially 10+ separate queries
  - Result: Already using best-practice aggregate() approach - no further optimization possible

## [1.0.2] - 2025-11-20

### Changed

- Dependencies
  - `django-eveuniverse` set to `1.6`
  - `django-ninja` set to `>=1.5,<2`
  - `allianceauth-app-utils` set to `>=1.3`
  - `django-esi` set to `>=8,<9`

### Removed

- `django-ninja` dependency pin `<1.5`
- csrf arg from `django-ninja`
- allow-direct-references

## [1.0.1] - 2025-11-13

### Added

- Temporary pin `django-ninja` to `django-ninja<=1.5`
  - https://github.com/vitalik/django-ninja/pull/1524

### Fixed

- Statistics is not showing when Data is `null`

### Changed

- Switch to OPENAPI3 ESI Client
  - Dependency `allianceauth-app-utils` set to `2b1`
  - Use new ETag System from `django-esi`
- Updated dependencies
- Updated README url for translations

## [1.0.0-beta.1] - 2025-11-03

> [!CAUTION]
>
> This is a BETA version, not intended for production use!
> Please test it in a test environment first and [report any issues].

### Changed

- Switch to OPENAPI3 ESI Client
- Updated dependencies
- Updated README url for translations

> [!WARNING]
> We changed the Payments Information, please use the following django command to migrate to new payments

```bash
python manage.py taxsystem_migrate_payments
```

## [0.7.2] - 21.10.2025

### Fixed

- Long loading issue in Payments View

## [0.7.1] - 21.10.2025

### Added

- Makefile System
- Custom Payments
- Contributing Guidelines

### Changed

- Open previous Modal if exist
- Updated Translations
- Updated Pre-Commit
- Updated npm
- moved `reloadStatistics` to bundle
- Updated ESI Status Check to fit new rate-limit guidelines

### Fixed

- CSS Issues
- Approve Modal not working in Admin View
- NoneType error in `division` property
- Payments should be Corporation related

## [0.7.0] - 22.08.2025

### Removed

- Smart Filter, Smart Group

### Added

- Filter System
  - Add Filter
  - Add Filter Set
  - Filter Modal
- Payments Manager Test

### Chaned

- Add Filter Menu to Administration

## [0.6.3] - 01.08.2025

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

[1.0.0-beta.1]: https://github.com/Geuthur/aa-taxsystem/compare/v0.7.2...v1.0.0-beta.1 "1.0.0-beta.1"
[in development]: https://github.com/Geuthur/aa-taxsystem/compare/v0.7.2...HEAD "In Development"
[report any issues]: https://github.com/Geuthur/aa-taxsystem/issues "report any issues"
