# AA Tax System - User Manual

## Table of Contents

1. [Introduction](#introduction)
1. [Getting Started](#getting-started)
1. [Adding Owners](#adding-owners)
1. [Payment System](#payment-system)
1. [Filter System](#filter-system)
1. [Account Management](#account-management)
1. [Administration](#administration)
1. [FAQ](#faq)

______________________________________________________________________

## Introduction

The AA Tax System is a comprehensive payment management system for Alliance Auth that allows corporations and alliances to manage member contributions, taxes, and payments efficiently. The system automates payment tracking, approval workflows, and provides detailed financial oversight for corporation and alliance leadership.

### Key Features

- **Multi-Owner Support**: Manage both Corporations and Alliances
- **Automated Payment Processing**: Filter-based automatic payment approval
- **Manual Approval Workflow**: Auditor review for unfiltered payments
- **Payment Tracking**: Monitor member deposits, due dates, and payment history
- **Dashboard Analytics**: Real-time statistics and financial overviews
- **Member Management**: Track member status and payment compliance
- **Flexible Filtering**: Customizable rules for automatic payment processing

______________________________________________________________________

## Getting Started

### Prerequisites

- Alliance Auth installation
- Required ESI scopes for corporation wallet access
- Appropriate permissions assigned to your character

### Required Permissions

- `taxsystem.basic_access` - Basic access to view tax system
- `taxsystem.manage_own_corp` - Manage your own corporation
- `taxsystem.manage_corps` - Manage all corporations
- `taxsystem.manage_own_alliance` - Manage your own alliance
- `taxsystem.manage_alliances` - Manage all alliances
- `taxsystem.create_access` - Add new corporations/alliances

______________________________________________________________________

## Adding Owners

### Adding a Corporation

1. Navigate to **Tax System** in the main menu
1. Click **Add Corporation** button
1. Authenticate with ESI (requires corporation director or CEO)
1. System will automatically:
   - Add the corporation to the tax system
   - Begin syncing wallet divisions
   - Initialize payment system for all members
   - Start tracking member activity

### Adding an Alliance

1. Navigate to **Tax System** in the main menu
1. Click **Add Alliance** button
1. Authenticate with ESI (requires alliance executor role)
1. Select the primary corporation for financial tracking
1. System will automatically:
   - Add the alliance to the tax system
   - Link to the designated corporation
   - Initialize payment tracking for all alliance members
   - Begin syncing data across all member corporations

### Owner Overview

The Owner Overview page displays all corporations and alliances you have access to manage:

- **Portrait**: Visual identification of the owner
- **Name**: Corporation or Alliance name with type badge
- **Status**: Active/Inactive indicator
- **Actions**:
  - **Payments**: View all payment transactions
  - **Manage**: Access management dashboard (requires manage permissions)

______________________________________________________________________

## Payment System

### How Payments Work

The Tax System tracks member contributions through ESI wallet journal entries. When a member sends ISK to the corporation/alliance wallet with a specific reason, the system:

1. **Detects the transaction** via ESI sync
1. **Applies filters** to determine if auto-approval is possible
1. **Routes for approval**:
   - **Auto-Approved**: Matches filter criteria → instantly credited
   - **Pending Review**: No filter match → requires auditor approval
1. **Updates account balance** upon approval
1. **Tracks payment history** for compliance monitoring

### Payment Status

- **Pending**: Awaiting auditor review
- **Approved**: Credited to member's account balance
- **Rejected**: Not credited, returned or noted
- **Automatic**: Auto-approved via filter rules

### Last Debit & Next Due

Each member account displays:

- **Last Debit**: When the most recent payment was processed (e.g., "2 days ago")
- **Next Due**: When the next payment is expected based on tax period (e.g., "in 5 days")

These dates help both members and auditors track payment compliance at a glance.

### Viewing Your Payments

Members can view their own payment history:

1. Navigate to **Tax System** → Select your corporation/alliance
1. Click **Own Payments** (no special permissions required)
1. View:
   - All your payment transactions
   - Payment dates and amounts
   - Approval status

**Note**: Own Payments only displays your transaction history. For detailed account information (balance, status, Last Debit, Next Due), click **Account** in the menu.

### Payment Statistics

The management dashboard displays:

- **Total Payments**: All recorded transactions
- **Pending Payments**: Awaiting auditor approval
- **Automatic Payments**: Auto-approved via filters
- **Manual Payments**: Auditor-approved transactions

______________________________________________________________________

## Filter System

### What are Filters?

Filters are automated rules that determine which payments should be automatically approved without manual auditor review. This significantly reduces administrative overhead for routine, expected payments.

### Filter Types

1. **Amount Filter**: Auto-approve payments of specific ISK amounts
1. **Reason Filter**: Auto-approve payments with specific transaction reasons/descriptions

### Filter Sets

Filters are organized into **Filter Sets** - logical groups of related filters that can be:

- **Enabled/Disabled**: Toggle entire filter sets on/off
- **Named & Described**: For organizational clarity
- **Managed Separately**: Different sets for different purposes

### Creating Filters

**Requirements**:

- Corporation: `taxsystem.manage_own_corp` or `taxsystem.manage_corps`
- Alliance: `taxsystem.manage_own_alliance` or `taxsystem.manage_alliances`

1. Navigate to **Manage** → **Manage Filters**
1. **Create a Filter Set** (if needed):
   - Click **Create Filter Set**
   - Enter a name (e.g., "Monthly Dues")
   - Add description (e.g., "Regular monthly corporation tax payments")
1. **Add Filters to the Set**:
   - Select the filter set
   - Choose filter type (Amount or Reason)
   - Choose match type (Exact or Contains)
   - Enter value:
     - **Amount**: `100000000` (100 million ISK)
     - **Reason**: `Monthly Tax` or `Corp Tax`
   - Click **Add Filter**

### Example Filter Configuration

**Scenario**: Monthly 100M ISK corporation tax with "Corp Tax" payment reason

```
Filter Set: "Monthly Corporation Tax"
├── Amount Filter: 100000000 ISK
└── Reason Filter: "Corp Tax"
```

**Result**: Any payment of exactly 100M ISK with "Corp Tax" as reason will be automatically approved.

### How Filtering Works

When a payment is received:

1. System checks if any **enabled** filter set matches
1. **All conditions** in a matching filter must be met (AND logic)
1. If matched → **Automatic Approval** → Instant credit
1. If not matched → **Pending Status** → Auditor must review

### Managing Filters

- **Edit Filter Set**: Update name/description
- **Enable/Disable Set**: Toggle without deleting
- **Delete Filter**: Remove specific filter rules
- **Delete Filter Set**: Remove entire group (requires confirmation)

______________________________________________________________________

## Account Management

### Account View

Each member has an account that tracks:

- **Account Name**: Character name
- **Owner**: Corporation or Alliance
- **Account Status**: Active, Inactive, Deactivated, or Missing
- **Balance Due**: Current deposit amount available
- **Payment Status**: Has Paid / Not Paid (visual indicator)
- **Last Debit**: Most recent payment (relative time)
- **Next Due**: When next payment is expected (relative time)
- **Joined**: Corporation/Alliance join date
- **Last Login**: Character's last login to EVE Online

### Accessing Your Account

1. Navigate to **Tax System** → **Account**
1. View your personal account details
1. No special permissions required

### Account Status Types

- **Active**: Member is current and in good standing
- **Inactive**: Member has not paid or is behind on payments
- **Deactivated**: Manually disabled by auditor (no longer required to pay)
- **Missing**: Character no longer in corporation/alliance

### Balance Due

The **Balance Due** represents the total ISK credited to your account through approved payments. This is your "account balance" that offsets required tax amounts set by leadership.

**Example**:

- Tax Amount: 100M ISK per month
- You paid: 300M ISK (approved)
- Balance Due: 300M ISK
- Covers: 3 months of tax

______________________________________________________________________

## Administration

### Management Dashboard

**Requirements**:

- Superuser: Access to all
- Corporation: `taxsystem.manage_own_corp` or `taxsystem.manage_corps`
- Alliance: `taxsystem.manage_own_alliance` or `taxsystem.manage_alliances`

The management dashboard provides:

1. **Owner Information**

   - Tax Amount (editable)
   - Tax Period (days, editable)
   - Activity status

1. **Update Status**

   - Last wallet sync
   - Last division sync
   - Last member sync
   - Last payment sync
   - Shows relative times (e.g., "updated 5 minutes ago")

1. **Wallet Divisions**

   - Division names (1-7)
   - Current balances
   - Total balance across all divisions

1. **Statistics**

   - Payment System Users (Active/Inactive/Deactivated)
   - Members (Mains/Alts/Unregistered)
   - Payment Counts (Total/Pending/Automatic/Manual)

### Tax Systen Management

View and manage all member tax accounts:

- **Account Information**: Character, status, balance
- **Payment Status**: Visual indicators (green = paid, red = unpaid)
- **Last Paid**: Most recent payment date
- **Next Due**: Expected next payment
- **Actions**:
  - Add manual payment
  - Switch user status (activate/deactivate)
  - View payment history

### Member Management

Track all corporation/alliance members:

- **Character Portrait & Name**
- **Status**: Active, Inactive, Missing, Unregistered
- **Joined Date**: When they joined the corp/alliance
- **Actions**:
  - Delete missing members (This enable tracking of leaving members)
  - View member details

### Approving Payments

**Requirements**:

- Corporation: `taxsystem.manage_own_corp` or `taxsystem.manage_corps`
- Alliance: `taxsystem.manage_own_alliance` or `taxsystem.manage_alliances`

1. Navigate to **Manage** → **Payments** section
1. View pending payments requiring approval
1. For each payment:
   - **Approve**: Credit to member account
   - **Reject**: Do not credit, log reason
   - **Delete**: Remove transaction (manual entries only)
   - **Undo**: Revert approval/rejection

### Manual Payment Entry

Auditors can manually add payments:

1. Navigate to **Manage** → **Tax Accounts**
1. Find the member account
1. Click **Add Payment**
1. Enter:
   - Amount
   - Reason/Description
1. Payment is automatically approved and credited

______________________________________________________________________

## FAQ

### For Members

**Q: How do I pay my corporation tax?**\
A: Send ISK to your corporation wallet with the specified payment reason in the transaction description. The system will automatically detect and process your payment.

**Q: Why is my payment still pending?**\
A: Your payment didn't match any automatic approval filters and requires manual auditor review.

**Q: Where can I see my payment history?**\
A: Navigate to Tax System → Own Payments to view all your transactions.

**Q: What does "Next Due" mean?**\
A: It shows when your next payment is expected based on the tax period set by leadership. This is informational and helps you plan ahead.

### For Auditors/Managers

**Q: How do I reduce manual payment approvals?**\
A: Set up filters for common payment amounts and reasons. This allows the system to automatically approve routine payments.

**Q: Can I retroactively approve old payments?**\
A: Yes, pending payments remain in the system until approved or rejected. You can process them at any time.

**Q: What happens if a member leaves the corporation?**\
A: Their account status changes to "Missing" and they are no longer tracked for future payments. Historical data remains for auditing purposes.

**Q: How often does the system sync with ESI?**\
A: Wallet and payment syncs occur automatically based on your Alliance Auth configuration. You can also trigger manual updates from the admin panel.

**Q: Can I export payment data?**\
A: Currently, data export is not available in the UI. Database queries can be used for advanced reporting (future feature planned).

### For Executives

**Q: What's the difference between Corporation and Alliance tax systems?**\
A: Both function identically. Alliance systems track members across all member corporations, while Corporation systems focus on a single corp.

**Q: How do I set the monthly tax amount?**\
A: Navigate to Manage dashboard and click on the Tax Amount field to edit it directly. This applies to all members.

**Q: Can different members have different tax amounts?**\
A: No, currently all members are subject to the same tax amount and period. Individual adjustments require manual payment entries or account deactivation.

______________________________________________________________________

## Support & Troubleshooting

### Common Issues

**Payments not appearing:**

- Check ESI token validity
- Verify wallet sync has completed
- Ensure transaction was sent to correct division

**Cannot access management dashboard:**

- Verify you have required permissions
- Confirm corporation was added to tax system

**Filter not working:**

- Ensure filter set is enabled
- Verify exact amount/reason match (case-sensitive)
- Check filter hasn't been deleted

### Getting Help

- Check Alliance Auth logs for errors
- Review corporation/alliance settings in admin panel
- Contact your Alliance Auth administrator
- Submit issues on GitHub: [github.com/Geuthur/aa-taxsystem](https://github.com/Geuthur/aa-taxsystem)

______________________________________________________________________

## Glossary

- **Owner**: Corporation or Alliance being managed
- **Payment System User**: Member account tracking payments
- **Auditor**: User with permission to approve/reject payments
- **Filter**: Automated rule for payment approval
- **Balance Due**: Total approved payments credited to member
- **Last Debit**: Most recent payment processed
- **Next Due**: Expected next payment date
- **Division**: Corporation wallet division (1-7)

______________________________________________________________________

*Last Updated: November 2025*\
*Version: 2.0.0*
