// Third Party
import { beforeEach, describe, expect, it, vi } from 'vitest';

// AA TaxSystem
import { apiClient } from '@/Api/Api';
import {
    loadMyPayments,
    loadPaymentDetails,
    loadPayments,
    manageBulkPaymentAction,
    managePaymentAction,
    paymentsQueryKeys,
} from '@/Api/calls/payments';

describe('paymentsQueryKeys', () => {
    it('provides the query keys of the area', () => {
        expect(paymentsQueryKeys.payments(10)).toEqual(['Payments', 10]);
        expect(paymentsQueryKeys.myPayments(10)).toEqual(['MyPayments', 10]);
        expect(paymentsQueryKeys.details(10, 42)).toEqual(['PaymentDetails', 10, 42]);
    });
});

describe('payments API calls', () => {
    beforeEach(() => {
        vi.restoreAllMocks();
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

type Method = 'GET' | 'POST';

/** Every call of `Api/calls/payments.ts`: [name, HTTP method, call, fixed text]. */
const calls: [string, Method, () => Promise<unknown>, string][] = [
    ['loadPayments', 'GET', () => loadPayments(1), 'Failed to load payments'],
    ['loadMyPayments', 'GET', () => loadMyPayments(1), 'Failed to load personal payments'],
    ['loadPaymentDetails', 'GET', () => loadPaymentDetails(1, 2), 'Failed to load payment details'],
    ['managePaymentAction', 'POST', () => managePaymentAction(1, 2, "approve"), 'Failed to approve payment'],
    ['manageBulkPaymentAction', 'POST', () => manageBulkPaymentAction(1, [2], "reject"), 'Failed to bulk reject payments'],
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
