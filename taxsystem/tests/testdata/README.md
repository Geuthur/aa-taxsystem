# Test Data Generation - Testing Guidelines

This directory contains all helper functions for creating test data in the TaxSystem test suite.

## ⚠️ CRITICAL: Test Prerequisites

**Every test MUST follow these requirements:**

### 1. Load Base Test Data

Always call these functions first in `setUpClass()`:

```python
@classmethod
def setUpClass(cls):
    super().setUpClass()
    load_allianceauth()  # Loads Alliance Auth base data
    load_eveuniverse()  # Loads EVE Universe data (characters, corps, etc.)
```

### 2. Create Test User via Factory Functions

**NEVER** create users directly! Always use the testdata factories from generate_owneraudit:

```python
# Create user with main character and required scopes
cls.user, cls.character_ownership = create_user_from_evecharacter_with_access(1001)
```

This function:

- Creates a user with proper authentication
- Assigns the character as main character
- Grants required ESI scopes
- Adds `taxsystem.basic_access` permission

### 3. Create CorporationOwner or AllianceOwner

Every test needs at least one owner. **Always use `create_corporation_owner_from_user()`:**

```python
# Create CorporationOwner from user's main character
cls.owner = create_corporation_owner_from_user(cls.user)
```

This function:

- Creates a CorporationOwner from the user's main character
- Sets up the proper eve_corporation relationship
- Ensures all required fields are populated

**Alternative methods (for specific use cases):**

```python
# Create CorporationOwner directly from character ID (creates user internally)
owner = create_corporation_owner_from_evecharacter(1001)

# Add additional character as CorporationOwner to existing user
owner2 = add_corporation_owner_to_user(cls.user, 1002)
```

For Alliance tests, use the dedicated Alliance factory functions:

```python
# Create AllianceOwner from user's main character
cls.alliance_owner, cls.corp_owner = create_alliance_owner_from_user(cls.user)

# Alternative: Create AllianceOwner directly from character ID
alliance_owner = create_alliance_owner_from_evecharacter(1001)
```

These functions:

- Create both CorporationOwner and AllianceOwner automatically
- Set up the proper eve_alliance and corporation relationships
- Ensure all required fields are populated

## Complete Test Template

```python
# Django
from django.test import TestCase

# AA TaxSystem
from taxsystem.models.corporation import CorporationOwner
from taxsystem.tests.testdata.load_allianceauth import load_allianceauth
from taxsystem.tests.testdata.load_eveuniverse import load_eveuniverse
from taxsystem.tests.testdata.generate_owneraudit import (
    create_user_from_evecharacter_with_access,
    create_corporation_owner_from_user,
)


class TestYourFeature(TestCase):
    """
    Test description.

    Prerequisites:
    - load_allianceauth() and load_eveuniverse() must be called first
    - Test user must be created via generate_owneraudit functions
    - At least one owner (CorporationOwner or AllianceOwner) must exist
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        # Step 1: Load base test data (REQUIRED)
        load_allianceauth()
        load_eveuniverse()

        # Step 2: Create test user with main character (REQUIRED)
        cls.user, cls.character_ownership = create_user_from_evecharacter_with_access(
            1001
        )

        # Step 3: Create CorporationOwner from user (REQUIRED)
        cls.owner = create_corporation_owner_from_user(cls.user)

    def test_your_feature(self):
        """Test your feature"""
        # Your test code here
        # Use: self.user, self.owner
        pass
```

## Available Testdata Functions

### User & Character Creation

- `create_user_from_evecharacter_with_access(character_id)` - Creates user with main character
- `add_auth_character_to_user(user, character_id)` - Adds alt character to existing user
- `add_corporation_owner_to_user(user, character_id)` - Adds character and creates CorporationOwner

### CorporationOwner Creation

- `create_corporation_owner_from_user(user)` - Creates CorporationOwner from user's main character
- `create_corporation_owner_from_evecharacter(character_id)` - Creates CorporationOwner from character ID

### AllianceOwner Creation

- `create_alliance_owner_from_user(user)` - Creates AllianceOwner (and CorporationOwner) from user's main character
- `create_alliance_owner_from_evecharacter(character_id)` - Creates AllianceOwner from character ID

### Payment System (Corporation)

- `create_payment_system(owner, **kwargs)` - Creates CorporationPaymentAccount
- `create_payment(account, **kwargs)` - Creates CorporationPayments
- `create_member(owner, **kwargs)` - Creates Members

### Payment System (Alliance)

- `create_alliance_payment_system(owner, **kwargs)` - Creates AlliancePaymentAccount
- `create_alliance_payment(account, **kwargs)` - Creates AlliancePayments

### Filters (Corporation)

- `create_filterset(owner, **kwargs)` - Creates CorporationFilterSet
- `create_filter(filter_set, **kwargs)` - Creates CorporationFilter

### Filters (Alliance)

- `create_alliance_filterset(owner, **kwargs)` - Creates AllianceFilterSet
- `create_alliance_filter(filter_set, **kwargs)` - Creates AllianceFilter

### Other Data

- Available in respective modules under `testdata/`

## Why These Requirements?

1. **load_allianceauth() / load_eveuniverse()**: Provides base EVE data (characters 1001-1003, corporations, alliances)
1. **generate_owneraudit functions**: Ensures proper user setup with permissions, scopes, and authentication
1. **Owner creation**: TaxSystem requires an owner (CorporationOwner or AllianceOwner) for all operations

## Common Mistakes to Avoid

❌ **DON'T:**

```python
# Creating user directly
cls.user = User.objects.create_user("test")

# Creating CorporationOwner directly
cls.owner = CorporationOwner.objects.create(
    name="Test Corp",
    eve_corporation=some_corp,
)

# Using get_or_create pattern
cls.owner = CorporationOwner.objects.filter(...).first()
if not cls.owner:
    cls.owner = CorporationOwner.objects.create(...)

# Skipping load functions
# Will cause: EveCharacter matching query does not exist
```

✅ **DO:**

```python
# Use testdata factory for user
cls.user, cls.character_ownership = create_user_from_evecharacter_with_access(1001)

# Use testdata factory for CorporationOwner
cls.owner = create_corporation_owner_from_user(cls.user)

# Or for AllianceOwner
cls.alliance_owner, cls.corp_owner = create_alliance_owner_from_user(cls.user)

# Always load base data first
load_allianceauth()
load_eveuniverse()
```

## Available Test Characters

From `load_eveuniverse()`:

- **1001**: Bruce Wayne (corporation_id: 2001)
- **1002**: Peter Parker (corporation_id: 2001)
- **1003**: Lex Luther (corporation_id: 2002)

Use these character IDs when creating test users.

## Questions?

Check existing tests in `taxsystem/tests/` for reference implementations:

- `test_performance.py` - Performance testing example
- `api/test_corporation.py` - API endpoint testing example
- `models/test_corporation.py` - Model testing example
