// Third Party
import { beforeEach, describe, expect, it, vi } from 'vitest';

// AA TaxSystem
import { apiClient } from '@/Api/Api';
import {
    dashboardQueryKeys,
    loadDashboard,
    updateOwnerSettings,
    updateTaxAmount,
    updateTaxPeriod,
} from '@/Api/calls/dashboard';

describe('dashboardQueryKeys', () => {
    it('provides the query keys of the area', () => {
        expect(dashboardQueryKeys.dashboard(10)).toEqual(['Dashboard', 10]);
    });
});

describe('dashboard API calls', () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    describe('loadDashboard', () => {
        it('calls the endpoint with its parameters and returns the data', async () => {
            // Test Data
            const response = { success: true };
            vi.spyOn(apiClient, 'GET').mockResolvedValueOnce({
                data: response,
                error: undefined,
                response: new Response(),
            } as never);

            // Test Action
            const result = await loadDashboard(10);

            // Expected Result
            expect(result).toEqual(response);
            expect(apiClient.GET).toHaveBeenCalledWith(
                '/taxsystem/api/corporation/{owner_id}/view/dashboard/',
                { params: { path: { owner_id: 10 } } },
            );
        });
    });
});

type Method = 'GET' | 'POST';

/** Every call of `Api/calls/dashboard.ts`: [name, HTTP method, call, fixed text]. */
const calls: [string, Method, () => Promise<unknown>, string][] = [
    ['loadDashboard', 'GET', () => loadDashboard(1), 'Failed to load dashboard'],
    ['updateOwnerSettings', 'POST', () => updateOwnerSettings(1, {}), 'Failed to update owner settings'],
    ['updateTaxAmount', 'POST', () => updateTaxAmount(1, 10), 'Failed to update tax amount'],
    ['updateTaxPeriod', 'POST', () => updateTaxPeriod(1, 30), 'Failed to update tax period'],
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
