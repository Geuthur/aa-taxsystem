// Third Party
import { beforeEach, describe, expect, it, vi } from 'vitest';

// AA TaxSystem
import { apiClient } from '@/Api/Api';
import {
    loadUserAccounts,
    userAccountsQueryKeys,
} from '@/Api/calls/userAccounts';

describe('userAccountsQueryKeys', () => {
    it('provides the query keys of the area', () => {
        expect(userAccountsQueryKeys.accounts).toEqual(['UserAccounts']);
    });
});

describe('userAccounts API calls', () => {
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
});

type Method = 'GET';

/** Every call of `Api/calls/userAccounts.ts`: [name, HTTP method, call, fixed text]. */
const calls: [string, Method, () => Promise<unknown>, string][] = [
    ['loadUserAccounts', 'GET', () => loadUserAccounts(), 'Failed to load user tax accounts'],
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
