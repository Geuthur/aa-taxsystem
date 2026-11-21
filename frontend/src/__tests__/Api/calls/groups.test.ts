// Third Party
import { beforeEach, describe, expect, it, vi } from 'vitest';

// AA TaxSystem
import { apiClient } from '@/Api/Api';
import {
    createGroup,
    deleteGroup,
    groupsQueryKeys,
    loadAvailableGroups,
    loadGroups,
} from '@/Api/calls/groups';

describe('groupsQueryKeys', () => {
    it('provides the query keys of the area', () => {
        expect(groupsQueryKeys.groups(10)).toEqual(['Groups', 10]);
        expect(groupsQueryKeys.available(10)).toEqual(['AvailableGroups', 10]);
    });
});

describe('groups API calls', () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    describe('deleteGroup', () => {
        it('calls the endpoint with its parameters and returns the data', async () => {
            // Test Data
            const response = { success: true };
            vi.spyOn(apiClient, 'POST').mockResolvedValueOnce({
                data: response,
                error: undefined,
                response: new Response(),
            } as never);

            // Test Action
            const result = await deleteGroup(10, 4, 'Removed');

            // Expected Result
            expect(result).toEqual(response);
            expect(apiClient.POST).toHaveBeenCalledWith(
                '/taxsystem/api/owner/{owner_id}/groups/{group_pk}/manage/delete/',
                { params: { path: { owner_id: 10, group_pk: 4 } }, body: { comment: 'Removed' } },
            );
        });
    });
});

type Method = 'GET' | 'POST';

/** Every call of `Api/calls/groups.ts`: [name, HTTP method, call, fixed text]. */
const calls: [string, Method, () => Promise<unknown>, string][] = [
    ['loadGroups', 'GET', () => loadGroups(1), 'Failed to load groups'],
    ['deleteGroup', 'POST', () => deleteGroup(1, 2), 'Failed to delete group'],
    ['loadAvailableGroups', 'GET', () => loadAvailableGroups(1), 'Failed to load available groups'],
    ['createGroup', 'POST', () => createGroup(1, {} as never), 'Failed to create group'],
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
