"""
Performance Testing Script for Tax System Optimization

Tests query counts and response times for all major endpoints
to validate Phase 1.2 optimization targets.
"""

# Standard Library
import time

# Django
from django.contrib.auth.models import User
from django.db import connection, reset_queries
from django.test import TestCase, override_settings

# AA TaxSystem
from taxsystem.api.helpers.common import (
    create_statistics_response,
    get_optimized_payments_queryset,
)
from taxsystem.api.helpers.statistics import (
    get_members_statistics,
    get_payment_system_statistics,
    get_payments_statistics,
)
from taxsystem.models.corporation import CorporationOwner, CorporationPayments, Members
from taxsystem.tests.testdata.generate_owneraudit import (
    create_user_from_evecharacter_with_access,
)
from taxsystem.tests.testdata.load_allianceauth import load_allianceauth
from taxsystem.tests.testdata.load_eveuniverse import load_eveuniverse


@override_settings(DEBUG=True)
class PerformanceTests(TestCase):
    """Test query counts and performance of optimized endpoints."""

    @classmethod
    def setUpTestData(cls):
        """Set up test data once for all tests."""
        load_allianceauth()
        load_eveuniverse()

        # Create test user with main character (character_id 1001)
        cls.user, cls.character_ownership = create_user_from_evecharacter_with_access(
            1001
        )

        # Get or create test owner from user's corporation
        cls.owner = CorporationOwner.objects.filter(
            eve_corporation=cls.user.profile.main_character.corporation
        ).first()

        if not cls.owner:
            # Create owner from user's main character corporation
            cls.owner = CorporationOwner.objects.create(
                name=cls.user.profile.main_character.corporation.corporation_name,
                eve_corporation=cls.user.profile.main_character.corporation,
            )

    def setUp(self):
        """Reset query counter before each test."""
        reset_queries()

    def _measure_performance(self, func, *args, **kwargs):
        """
        Measure query count and execution time for a function.

        Returns:
            tuple: (result, query_count, execution_time_ms)
        """
        reset_queries()
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        query_count = len(connection.queries)
        execution_time = (end_time - start_time) * 1000  # Convert to ms

        return result, query_count, execution_time

    def test_payments_statistics_query_count(self):
        """Test that payment statistics uses single query."""
        if not self.owner:
            self.skipTest("No test owner available")

        result, query_count, exec_time = self._measure_performance(
            get_payments_statistics, self.owner
        )

        self.assertEqual(
            query_count,
            1,
            f"Expected 1 query for payments statistics, got {query_count}",
        )
        self.assertIsNotNone(result)
        print(f"\n✅ Payments Statistics: {query_count} query, {exec_time:.2f}ms")

    def test_payment_system_statistics_query_count(self):
        """Test that payment system statistics uses single query."""
        if not self.owner:
            self.skipTest("No test owner available")

        result, query_count, exec_time = self._measure_performance(
            get_payment_system_statistics, self.owner
        )

        self.assertEqual(
            query_count,
            1,
            f"Expected 1 query for payment system statistics, got {query_count}",
        )
        self.assertIsNotNone(result)
        print(f"✅ Payment System Statistics: {query_count} query, {exec_time:.2f}ms")

    def test_members_statistics_query_count(self):
        """Test that members statistics uses single query."""
        if not self.owner:
            self.skipTest("No test owner available")

        result, query_count, exec_time = self._measure_performance(
            get_members_statistics, self.owner
        )

        self.assertEqual(
            query_count,
            1,
            f"Expected 1 query for members statistics, got {query_count}",
        )
        self.assertIsNotNone(result)
        print(f"✅ Members Statistics: {query_count} query, {exec_time:.2f}ms")

    def test_full_statistics_response_query_count(self):
        """Test that full statistics response uses 3 queries (1 per table)."""
        if not self.owner:
            self.skipTest("No test owner available")

        result, query_count, exec_time = self._measure_performance(
            create_statistics_response, self.owner
        )

        self.assertEqual(
            query_count,
            3,
            f"Expected 3 queries for full statistics (1 per table), got {query_count}",
        )
        self.assertIsNotNone(result)
        print(f"✅ Full Statistics Response: {query_count} queries, {exec_time:.2f}ms")

    def test_optimized_payments_queryset(self):
        """Test that optimized payments queryset uses select_related efficiently."""
        if not self.owner:
            self.skipTest("No test owner available")

        # Get optimized queryset with actual owner_id value
        reset_queries()
        owner_id_value = self.owner.eve_corporation.corporation_id
        queryset = get_optimized_payments_queryset(
            CorporationPayments, self.owner, owner_id_value
        )

        # Accessing the queryset doesn't execute query yet
        initial_queries = len(connection.queries)
        self.assertEqual(
            initial_queries, 0, "Queryset should not execute before evaluation"
        )

        # Evaluate queryset and access related objects
        start_time = time.time()
        payments = list(queryset[:10])  # Get first 10 payments
        for payment in payments:
            # Access related objects that should be prefetched
            _ = payment.account
            if hasattr(payment.account, "user"):
                _ = payment.account.user
                if hasattr(payment.account.user, "profile"):
                    _ = payment.account.user.profile
                    if hasattr(payment.account.user.profile, "main_character"):
                        _ = payment.account.user.profile.main_character

        end_time = time.time()
        exec_time = (end_time - start_time) * 1000
        query_count = len(connection.queries)

        # Should be minimal queries due to select_related
        # Expected: 1 query for payments + select_related data
        self.assertLessEqual(
            query_count,
            2,
            f"Expected ≤2 queries with select_related, got {query_count}",
        )
        print(
            f"✅ Optimized Payments Queryset: {query_count} queries, {exec_time:.2f}ms for 10 payments"
        )

    def test_members_queryset_optimization(self):
        """Test that members queryset uses select_related for owner."""
        if not self.owner:
            self.skipTest("No test owner available")

        reset_queries()
        start_time = time.time()

        # Get members with select_related
        members = Members.objects.filter(owner=self.owner).select_related("owner")[:10]

        # Access related owner for each member
        for member in members:
            _ = member.owner.name

        end_time = time.time()
        exec_time = (end_time - start_time) * 1000
        query_count = len(connection.queries)

        # Should be 1 query with select_related
        self.assertEqual(
            query_count,
            1,
            f"Expected 1 query with select_related('owner'), got {query_count}",
        )
        print(
            f"✅ Members Queryset: {query_count} query, {exec_time:.2f}ms for 10 members"
        )

    def test_performance_summary(self):
        """Print performance summary for all optimizations."""
        if not self.owner:
            self.skipTest("No test owner available")

        print("\n" + "=" * 70)
        print("PERFORMANCE TEST SUMMARY - Phase 1.2 Optimizations")
        print("=" * 70)

        # Test statistics
        _, stats_queries, stats_time = self._measure_performance(
            create_statistics_response, self.owner
        )

        # Test payments
        reset_queries()
        owner_id_value = self.owner.eve_corporation.corporation_id
        payments_qs = get_optimized_payments_queryset(
            CorporationPayments, self.owner, owner_id_value
        )
        start = time.time()
        list(payments_qs[:20])
        payments_time = (time.time() - start) * 1000
        payments_queries = len(connection.queries)

        # Test members
        reset_queries()
        start = time.time()
        list(Members.objects.filter(owner=self.owner).select_related("owner")[:20])
        members_time = (time.time() - start) * 1000
        members_queries = len(connection.queries)

        print("\n📊 Query Counts:")
        print(f"  - Dashboard Statistics: {stats_queries} queries (Target: 3)")
        print(f"  - Payments (20 items): {payments_queries} queries (Target: ≤2)")
        print(f"  - Members (20 items): {members_queries} queries (Target: 1)")

        print("\n⏱️  Response Times:")
        print(f"  - Dashboard Statistics: {stats_time:.2f}ms")
        print(f"  - Payments (20 items): {payments_time:.2f}ms")
        print(f"  - Members (20 items): {members_time:.2f}ms")

        print("\n✅ Optimization Status:")
        print(
            f"  - N+1 Query Fixes: {'✅ PASSED' if payments_queries <= 2 and members_queries == 1 else '❌ FAILED'}"
        )
        print(
            f"  - Statistics Aggregation: {'✅ PASSED' if stats_queries == 3 else '❌ FAILED'}"
        )
        print("  - Database Indexes: ✅ IMPLEMENTED (Runtime testing required)")

        print("\n" + "=" * 70)

        # Assert all targets met
        self.assertEqual(stats_queries, 3, "Statistics should use 3 queries")
        self.assertLessEqual(payments_queries, 2, "Payments should use ≤2 queries")
        self.assertEqual(members_queries, 1, "Members should use 1 query")
