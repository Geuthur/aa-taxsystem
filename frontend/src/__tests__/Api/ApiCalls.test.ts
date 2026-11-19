// Third Party
import { beforeEach, describe, expect, it, vi } from 'vitest';

// AA TaxSystem
import { apiClient } from '@/Api/Api';
import {
    addCustomPayment,
    approvePayment,
    createFilter,
    createFilterSet,
    createGroup,
    deleteAdministrationOwner,
    deleteFilter,
    deleteFilterSet,
    deleteGroup,
    deleteMember,
    deleteOwner,
    deletePayment,
    loadAdministrationOwnerInspect,
    loadAdministrationOwners,
    loadAdminLogs,
    loadAvailableGroups,
    loadDashboard,
    loadFilters,
    loadFilterSets,
    loadGroups,
    loadMemberPayments,
    loadMembers,
    loadMyPayments,
    loadOverview,
    loadPaymentDetails,
    loadPayments,
    loadSettingsOwners,
    loadTaxAccounts,
    loadUserAccounts,
    manageBulkPaymentAction,
    managePaymentAction,
    rejectPayment,
    runAdminTasks,
    switchFilterSet,
    switchTaxAccount,
    triggerAdministrationOwnerUpdate,
    triggerOwnerUpdate,
    triggerUpdateAllTaxOwners,
    undoPayment,
    updateOwnerSettings,
    updateTaxAmount,
    updateTaxPeriod,
} from '@/Api/ApiCalls';

describe('General API client functions', () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    describe('loadUserAccounts', () => {
        it('calls /taxsystem/api/user/accounts/ and returns account list', async () => {
            // Test Data
            const mockAccounts = [
                {
                    id: 1,
                    name: 'Test Pilot',
                    owner_id: 10,
                    owner_name: 'Test Corp',
                    owner_type: 'corporation',
                    deposit: 5000000,
                    tax_amount: 10000000,
                    tax_period: 30,
                    has_paid: false,
                    status: 'active',
                    status_display: 'Active',
                    open_invoices: 1,
                },
            ];
            vi.spyOn(apiClient, 'GET').mockResolvedValueOnce({
                data: mockAccounts,
                error: undefined,
                response: new Response(),
            } as never);

            // Test Action
            const result = await loadUserAccounts();

            // Expected Result
            expect(result).toEqual(mockAccounts);
            expect(apiClient.GET).toHaveBeenCalledWith('/taxsystem/api/user/accounts/');
        });

        it('throws error when GET fails or returns no data', async () => {
            // Test Data
            vi.spyOn(apiClient, 'GET').mockResolvedValueOnce({
                data: undefined,
                error: { status: 500 },
                response: new Response(),
            } as never);

            // Test Action & Expected Result
            await expect(loadUserAccounts()).rejects.toThrow('Failed to load user tax accounts');
        });
    });

    describe('addCustomPayment', () => {
        it('posts custom payment payload and returns success', async () => {
            // Test Data
            const payload = { amount: 25000000, comment: 'Monthly dues bonus' };
            vi.spyOn(apiClient, 'POST').mockResolvedValueOnce({
                data: { success: true, message: 'Payment added' },
                error: undefined,
                response: new Response(),
            } as never);

            // Test Action
            const result = await addCustomPayment(10, 42, payload);

            // Expected Result
            expect(result).toEqual({ success: true, message: 'Payment added' });
            expect(apiClient.POST).toHaveBeenCalledWith(
                '/taxsystem/api/owner/{owner_id}/account/{account_pk}/manage/add-payment/',
                {
                    params: { path: { owner_id: 10, account_pk: 42 } },
                    body: payload,
                },
            );
        });

        it('throws error when POST fails or returns no data', async () => {
            // Test Data
            vi.spyOn(apiClient, 'POST').mockResolvedValueOnce({
                data: undefined,
                error: { status: 400 },
                response: new Response(),
            } as never);

            // Test Action & Expected Result
            await expect(addCustomPayment(10, 42, { amount: 100, comment: 'test' })).rejects.toThrow('Failed to add custom payment');
        });
    });

    describe('deletePayment', () => {
        it('calls delete-payment with comment body and returns success', async () => {
            // Test Data
            vi.spyOn(apiClient, 'POST').mockResolvedValueOnce({
                data: { success: true, message: 'Payment deleted' },
                error: undefined,
                response: new Response(),
            } as never);

            // Test Action
            const result = await deletePayment(10, 42, 'Removed duplicate');

            // Expected Result
            expect(result).toEqual({ success: true, message: 'Payment deleted' });
            expect(apiClient.POST).toHaveBeenCalledWith(
                '/taxsystem/api/owner/{owner_id}/payment/{payment_pk}/manage/delete-payment/',
                {
                    params: { path: { owner_id: 10, payment_pk: 42 } },
                    body: { comment: 'Removed duplicate' },
                },
            );
        });

        it('throws error when POST fails or returns no data', async () => {
            // Test Data
            vi.spyOn(apiClient, 'POST').mockResolvedValueOnce({
                data: undefined,
                error: { status: 400 },
                response: new Response(),
            } as never);

            // Test Action & Expected Result
            await expect(deletePayment(10, 42)).rejects.toThrow('Failed to delete payment');
        });
    });

    describe('manageBulkPaymentAction', () => {
        it('calls POST endpoint with owner_id and bulk payload', async () => {
            // Test Data
            const mockResponse = {
                success: true,
                message: '3 payments processed successfully',
                processed_count: 3,
                total_count: 3,
            };
            vi.spyOn(apiClient, 'POST').mockResolvedValueOnce({
                data: mockResponse,
                error: undefined,
                response: new Response(),
            } as never);

            // Test Action
            const result = await manageBulkPaymentAction(10, [101, 102, 103], 'approve', 'Bulk test');

            // Expected Result
            expect(result).toEqual(mockResponse);
            expect(apiClient.POST).toHaveBeenCalledWith(
                '/taxsystem/api/owner/{owner_id}/manage/payments/bulk-action/',
                {
                    params: { path: { owner_id: 10 } },
                    body: {
                        payment_ids: [101, 102, 103],
                        action: 'approve',
                        comment: 'Bulk test',
                    },
                },
            );
        });

        it('throws error when POST fails or returns no data', async () => {
            // Test Data
            vi.spyOn(apiClient, 'POST').mockResolvedValueOnce({
                data: undefined,
                error: { status: 400 },
                response: new Response(),
            } as never);

            // Test Action & Expected Result
            await expect(
                manageBulkPaymentAction(10, [101], 'reject'),
            ).rejects.toThrow('Failed to bulk reject payments');
        });
    });
});

type Method = 'GET' | 'POST' | 'DELETE';

/** Every call of `ApiCalls.ts`: [name, HTTP method, call, fixed text]. */
const calls: [string, Method, () => Promise<unknown>, string][] = [
    ['loadOverview', 'GET', () => loadOverview(), 'Failed to load overview'],
    ['loadDashboard', 'GET', () => loadDashboard(1), 'Failed to load dashboard'],
    ['loadTaxAccounts', 'GET', () => loadTaxAccounts(1), 'Failed to load tax accounts'],
    ['switchTaxAccount', 'POST', () => switchTaxAccount(1, 2), 'Failed to switch tax account'],
    ['updateOwnerSettings', 'POST', () => updateOwnerSettings(1, {}), 'Failed to update owner settings'],
    ['updateTaxAmount', 'POST', () => updateTaxAmount(1, 10), 'Failed to update tax amount'],
    ['updateTaxPeriod', 'POST', () => updateTaxPeriod(1, 30), 'Failed to update tax period'],
    ['loadMembers', 'GET', () => loadMembers(1), 'Failed to load members'],
    ['deleteMember', 'POST', () => deleteMember(1, 2), 'Failed to delete member'],
    ['loadPayments', 'GET', () => loadPayments(1), 'Failed to load payments'],
    ['loadMyPayments', 'GET', () => loadMyPayments(1), 'Failed to load personal payments'],
    ['loadPaymentDetails', 'GET', () => loadPaymentDetails(1, 2), 'Failed to load payment details'],
    ['managePaymentAction', 'POST', () => managePaymentAction(1, 2, "approve"), 'Failed to approve payment'],
    ['manageBulkPaymentAction', 'POST', () => manageBulkPaymentAction(1, [2], "reject"), 'Failed to bulk reject payments'],
    ['approvePayment', 'POST', () => approvePayment(1, 2), 'Failed to approve payment'],
    ['rejectPayment', 'POST', () => rejectPayment(1, 2), 'Failed to reject payment'],
    ['undoPayment', 'POST', () => undoPayment(1, 2), 'Failed to undo payment'],
    ['deletePayment', 'POST', () => deletePayment(1, 2), 'Failed to delete payment'],
    ['loadFilterSets', 'GET', () => loadFilterSets(1), 'Failed to load filter sets'],
    ['loadFilters', 'GET', () => loadFilters(1, 2), 'Failed to load filters'],
    ['deleteFilter', 'POST', () => deleteFilter(1, 2), 'Failed to delete filter'],
    ['deleteFilterSet', 'POST', () => deleteFilterSet(1, 2), 'Failed to delete filter set'],
    ['switchFilterSet', 'POST', () => switchFilterSet(1, 2), 'Failed to switch filter set'],
    ['loadGroups', 'GET', () => loadGroups(1), 'Failed to load groups'],
    ['deleteGroup', 'POST', () => deleteGroup(1, 2), 'Failed to delete group'],
    ['loadAdminLogs', 'GET', () => loadAdminLogs(1), 'Failed to load admin logs'],
    ['runAdminTasks', 'POST', () => runAdminTasks({} as never), 'Failed to run admin tasks'],
    ['loadMemberPayments', 'GET', () => loadMemberPayments(1, 2), 'Failed to load member payments'],
    ['createFilterSet', 'POST', () => createFilterSet(1, {} as never), 'Failed to create filter set'],
    ['createFilter', 'POST', () => createFilter(1, {} as never), 'Failed to create filter'],
    ['loadAvailableGroups', 'GET', () => loadAvailableGroups(1), 'Failed to load available groups'],
    ['createGroup', 'POST', () => createGroup(1, {} as never), 'Failed to create group'],
    ['loadUserAccounts', 'GET', () => loadUserAccounts(), 'Failed to load user tax accounts'],
    ['addCustomPayment', 'POST', () => addCustomPayment(1, 2, {} as never), 'Failed to add custom payment'],
    ['loadAdministrationOwners', 'GET', () => loadAdministrationOwners(), 'Failed to load administration owners'],
    ['triggerAdministrationOwnerUpdate', 'POST', () => triggerAdministrationOwnerUpdate({ ownerType: "corporation", ownerId: 1 }), 'Failed to trigger update'],
    ['deleteAdministrationOwner', 'DELETE', () => deleteAdministrationOwner({ ownerType: "corporation", ownerId: 1 }), 'Failed to delete owner'],
    ['loadAdministrationOwnerInspect', 'GET', () => loadAdministrationOwnerInspect({ ownerType: "corporation", ownerId: 1 }), 'Failed to inspect owner dashboard'],
    ['triggerOwnerUpdate', 'POST', () => triggerOwnerUpdate({ ownerId: 1 }), 'Failed to trigger update'],
    ['deleteOwner', 'DELETE', () => deleteOwner(1), 'Failed to delete owner'],
    ['loadSettingsOwners', 'GET', () => loadSettingsOwners(), 'Failed to load settings owners'],
    ['triggerUpdateAllTaxOwners', 'POST', () => triggerUpdateAllTaxOwners(), 'Failed to trigger update all owners'],
];

const failWith = (method: Method, error: unknown) =>
    vi.spyOn(apiClient, method).mockResolvedValueOnce({
        data: undefined,
        error,
        response: new Response(),
    } as never);

describe('API error messages', () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    describe.each(calls)('%s', (_name, method, call, fixedText) => {
        it('should throw the message of the API when the request fails', async () => {
            // Test Data
            failWith(method, { error: 'Permission Denied' });

            // Test Action & Expected Result
            await expect(call()).rejects.toThrow('Permission Denied');
        });

        it('should throw the fixed text when the API sent no message', async () => {
            // Test Data
            failWith(method, {});

            // Test Action & Expected Result
            await expect(call()).rejects.toThrow(fixedText);
        });
    });
});
