// Third Party
import { beforeEach, describe, expect, it, vi } from 'vitest';

// AA TaxSystem
import { apiClient } from '@/Api/Api';
import {
    administrationQueryKeys,
    deleteAdministrationOwner,
    loadAdministrationOwnerInspect,
    loadAdministrationOwners,
    runAdminTasks,
    triggerAdministrationOwnerUpdate,
} from '@/Api/calls/administration';

describe('administrationQueryKeys', () => {
    it('provides the query keys of the area', () => {
        expect(administrationQueryKeys.owners).toEqual(['AdministrationOwners']);
        expect(administrationQueryKeys.ownerInspect('alliance', 10)).toEqual(['AdministrationOwnerInspect', 'alliance', 10]);
    });
});

describe('administration API calls', () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    describe('loadAdministrationOwnerInspect', () => {
        it('calls the endpoint with its parameters and returns the data', async () => {
            // Test Data
            const response = { success: true };
            vi.spyOn(apiClient, 'GET').mockResolvedValueOnce({
                data: response,
                error: undefined,
                response: new Response(),
            } as never);

            // Test Action
            const result = await loadAdministrationOwnerInspect({ ownerType: 'alliance', ownerId: 99 });

            // Expected Result
            expect(result).toEqual(response);
            expect(apiClient.GET).toHaveBeenCalledWith(
                '/taxsystem/api/administration/owners/{owner_type}/{owner_id}/inspect/',
                { params: { path: { owner_type: 'alliance', owner_id: 99 } } },
            );
        });
    });
});

type Method = 'DELETE' | 'GET' | 'POST';

/** Every call of `Api/calls/administration.ts`: [name, HTTP method, call, fixed text]. */
const calls: [string, Method, () => Promise<unknown>, string][] = [
    ['runAdminTasks', 'POST', () => runAdminTasks({} as never), 'Failed to run admin tasks'],
    ['loadAdministrationOwners', 'GET', () => loadAdministrationOwners(), 'Failed to load administration owners'],
    ['triggerAdministrationOwnerUpdate', 'POST', () => triggerAdministrationOwnerUpdate({ ownerType: "corporation", ownerId: 1 }), 'Failed to trigger update'],
    ['deleteAdministrationOwner', 'DELETE', () => deleteAdministrationOwner({ ownerType: "corporation", ownerId: 1 }), 'Failed to delete owner'],
    ['loadAdministrationOwnerInspect', 'GET', () => loadAdministrationOwnerInspect({ ownerType: "corporation", ownerId: 1 }), 'Failed to inspect owner dashboard'],
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
