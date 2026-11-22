// Third Party
import { beforeEach, describe, expect, it, vi } from 'vitest';

// AA TaxSystem
import { apiClient } from '@/Api/Api';
import {
    deleteOwner,
    loadSettingsOwners,
    settingsQueryKeys,
    triggerOwnerUpdate,
    triggerUpdateAllTaxOwners,
} from '@/Api/calls/settings';

describe('settingsQueryKeys', () => {
    it('provides the query keys of the area', () => {
        expect(settingsQueryKeys.owners).toEqual(['SettingsOwners']);
    });
});

describe('settings API calls', () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    describe('triggerOwnerUpdate', () => {
        it('calls the endpoint with its parameters and returns the data', async () => {
            // Test Data
            const response = { success: true };
            vi.spyOn(apiClient, 'POST').mockResolvedValueOnce({
                data: response,
                error: undefined,
                response: new Response(),
            } as never);

            // Test Action
            const result = await triggerOwnerUpdate({ ownerId: 10, forceRefresh: true });

            // Expected Result
            expect(result).toEqual(response);
            expect(apiClient.POST).toHaveBeenCalledWith(
                '/taxsystem/api/owner/{owner_id}/update/',
                { params: { path: { owner_id: 10 } }, body: { force_refresh: true } },
            );
        });
    });
});

type Method = 'DELETE' | 'GET' | 'POST';

/** Every call of `Api/calls/settings.ts`: [name, HTTP method, call, fixed text]. */
const calls: [string, Method, () => Promise<unknown>, string][] = [
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
