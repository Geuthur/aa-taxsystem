// Third Party
import { beforeEach, describe, expect, it, vi } from 'vitest';

// AA TaxSystem
import { apiClient } from '@/Api/Api';
import {
    addCustomPayment,
    deletePayment,
    loadMenu,
    loadUserAccounts,
    loadUserData,
    loadUserSettings,
    updateUserSettings,
} from '@/Api/ApiCalls';

describe('General API client functions', () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    describe('loadUserData', () => {
        it('returns user data on successful GET', async () => {
            const mockUser = { user_id: 1, character_id: 42, character_name: 'Test Pilot' };
            vi.spyOn(apiClient, 'GET').mockResolvedValueOnce({
                data: mockUser,
                error: undefined,
                response: new Response(),
            } as never);

            const result = await loadUserData();
            expect(result).toEqual({ user: mockUser });
            expect(apiClient.GET).toHaveBeenCalledWith('/taxsystem/api/user/');
        });

        it('throws error when GET fails or returns no data', async () => {
            vi.spyOn(apiClient, 'GET').mockResolvedValueOnce({
                data: undefined,
                error: { status: 500 },
                response: new Response(),
            } as never);

            await expect(loadUserData()).rejects.toThrow('Failed to load user data');
        });
    });

    describe('loadMenu', () => {
        it('calls /taxsystem/api/menu/ and returns data', async () => {
            const mockMenu = { left_links: [], right_links: [] };
            vi.spyOn(apiClient, 'GET').mockResolvedValueOnce({
                data: mockMenu,
                error: undefined,
                response: new Response(),
            } as never);

            const result = await loadMenu();
            expect(result).toEqual(mockMenu);
            expect(apiClient.GET).toHaveBeenCalledWith('/taxsystem/api/menu/');
        });
    });

    describe('loadUserSettings', () => {
        it('returns settings from the typed GET endpoint', async () => {
            const settings = { disable_notifications: true };
            vi.spyOn(apiClient, 'GET').mockResolvedValueOnce({
                data: settings,
                error: undefined,
                response: new Response(),
            } as never);

            const result = await loadUserSettings();
            expect(result).toEqual(settings);
            expect(apiClient.GET).toHaveBeenCalledWith('/taxsystem/api/settings/');
        });
    });

    describe('updateUserSettings', () => {
        it('submits JSON to the typed PUT endpoint', async () => {
            const settings = { disable_notifications: true };
            vi.spyOn(apiClient, 'PUT').mockResolvedValueOnce({
                data: settings,
                error: undefined,
                response: new Response(),
            } as never);

            const result = await updateUserSettings(settings);
            expect(result).toEqual(settings);
            expect(apiClient.PUT).toHaveBeenCalledWith('/taxsystem/api/settings/', {
                body: settings,
            });
        });

        it('throws error when update fails', async () => {
            vi.spyOn(apiClient, 'PUT').mockResolvedValueOnce({
                data: undefined,
                error: { status: 403 },
                response: new Response(),
            } as never);

            await expect(updateUserSettings({ disable_notifications: false })).rejects.toThrow('Failed to update user settings');
        });
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
});
