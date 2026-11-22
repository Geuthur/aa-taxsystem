// Third Party
import { beforeEach, describe, expect, it, vi } from 'vitest';

// AA TaxSystem
import { apiClient } from '@/Api/Api';
import {
    deleteMember,
    loadMemberPayments,
    loadMembers,
    membersQueryKeys,
} from '@/Api/calls/members';

describe('membersQueryKeys', () => {
    it('provides the query keys of the area', () => {
        expect(membersQueryKeys.members(10)).toEqual(['Members', 10]);
        expect(membersQueryKeys.payments(10, 2001)).toEqual(['MemberPayments', 10, 2001]);
    });
});

describe('members API calls', () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    describe('loadMemberPayments', () => {
        it('calls the endpoint with its parameters and returns the data', async () => {
            // Test Data
            const response = { success: true };
            vi.spyOn(apiClient, 'GET').mockResolvedValueOnce({
                data: response,
                error: undefined,
                response: new Response(),
            } as never);

            // Test Action
            const result = await loadMemberPayments(10, 2001);

            // Expected Result
            expect(result).toEqual(response);
            expect(apiClient.GET).toHaveBeenCalledWith(
                '/taxsystem/api/owner/{owner_id}/character/{character_id}/view/payments/',
                { params: { path: { owner_id: 10, character_id: 2001 } } },
            );
        });
    });
});

type Method = 'GET' | 'POST';

/** Every call of `Api/calls/members.ts`: [name, HTTP method, call, fixed text]. */
const calls: [string, Method, () => Promise<unknown>, string][] = [
    ['loadMembers', 'GET', () => loadMembers(1), 'Failed to load members'],
    ['deleteMember', 'POST', () => deleteMember(1, 2), 'Failed to delete member'],
    ['loadMemberPayments', 'GET', () => loadMemberPayments(1, 2), 'Failed to load member payments'],
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
