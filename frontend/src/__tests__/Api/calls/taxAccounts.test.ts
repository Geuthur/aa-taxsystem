// Third Party
import { beforeEach, describe, expect, it, vi } from 'vitest';

// AA TaxSystem
import { apiClient } from '@/Api/Api';
import {
    addCustomPayment,
    loadTaxAccounts,
    switchTaxAccount,
    taxAccountsQueryKeys,
} from '@/Api/calls/taxAccounts';

describe('taxAccountsQueryKeys', () => {
    it('provides the query keys of the area', () => {
        expect(taxAccountsQueryKeys.accounts(10)).toEqual(['TaxAccounts', 10]);
    });
});

describe('taxAccounts API calls', () => {
    beforeEach(() => {
        vi.restoreAllMocks();
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
});

type Method = 'GET' | 'POST';

/** Every call of `Api/calls/taxAccounts.ts`: [name, HTTP method, call, fixed text]. */
const calls: [string, Method, () => Promise<unknown>, string][] = [
    ['loadTaxAccounts', 'GET', () => loadTaxAccounts(1), 'Failed to load tax accounts'],
    ['switchTaxAccount', 'POST', () => switchTaxAccount(1, 2), 'Failed to switch tax account'],
    ['addCustomPayment', 'POST', () => addCustomPayment(1, 2, {} as never), 'Failed to add custom payment'],
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
