// Third Party
import { beforeEach, describe, expect, it, vi } from 'vitest';

// AA TaxSystem
import { apiClient } from '@/Api/Api';
import {
    loadOverview,
    overviewQueryKeys,
} from '@/Api/calls/overview';

describe('overviewQueryKeys', () => {
    it('provides the query keys of the area', () => {
        expect(overviewQueryKeys.overview).toEqual(['Overview']);
    });
});

describe('overview API calls', () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    describe('loadOverview', () => {
        it('calls the endpoint with its parameters and returns the data', async () => {
            // Test Data
            const response = { success: true };
            vi.spyOn(apiClient, 'GET').mockResolvedValueOnce({
                data: response,
                error: undefined,
                response: new Response(),
            } as never);

            // Test Action
            const result = await loadOverview();

            // Expected Result
            expect(result).toEqual(response);
            expect(apiClient.GET).toHaveBeenCalledWith(
                '/taxsystem/api/overview/'
            );
        });
    });
});

type Method = 'GET';

/** Every call of `Api/calls/overview.ts`: [name, HTTP method, call, fixed text]. */
const calls: [string, Method, () => Promise<unknown>, string][] = [
    ['loadOverview', 'GET', () => loadOverview(), 'Failed to load overview'],
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
