// Third Party
import { beforeEach, describe, expect, it, vi } from 'vitest';

// AA TaxSystem
import { apiClient } from '@/Api/Api';
import {
    historyQueryKeys,
    loadAdminLogs,
} from '@/Api/calls/history';

describe('historyQueryKeys', () => {
    it('provides the query keys of the area', () => {
        expect(historyQueryKeys.adminLogs(10)).toEqual(['AdminLogs', 10]);
    });
});

describe('history API calls', () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    describe('loadAdminLogs', () => {
        it('calls the endpoint with its parameters and returns the data', async () => {
            // Test Data
            const response = { success: true };
            vi.spyOn(apiClient, 'GET').mockResolvedValueOnce({
                data: response,
                error: undefined,
                response: new Response(),
            } as never);

            // Test Action
            const result = await loadAdminLogs(10);

            // Expected Result
            expect(result).toEqual(response);
            expect(apiClient.GET).toHaveBeenCalledWith(
                '/taxsystem/api/owner/{owner_id}/view/admin-history/',
                { params: { path: { owner_id: 10 } } },
            );
        });
    });
});

type Method = 'GET';

/** Every call of `Api/calls/history.ts`: [name, HTTP method, call, fixed text]. */
const calls: [string, Method, () => Promise<unknown>, string][] = [
    ['loadAdminLogs', 'GET', () => loadAdminLogs(1), 'Failed to load admin logs'],
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
