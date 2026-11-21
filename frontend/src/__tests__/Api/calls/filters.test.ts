// Third Party
import { beforeEach, describe, expect, it, vi } from 'vitest';

// AA TaxSystem
import { apiClient } from '@/Api/Api';
import {
    createFilter,
    createFilterSet,
    deleteFilter,
    deleteFilterSet,
    filtersQueryKeys,
    loadFilters,
    loadFilterSets,
    switchFilterSet,
} from '@/Api/calls/filters';

describe('filtersQueryKeys', () => {
    it('provides the query keys of the area', () => {
        expect(filtersQueryKeys.filterSets(10)).toEqual(['FilterSets', 10]);
        expect(filtersQueryKeys.filters(10, 3)).toEqual(['Filters', 10, 3]);
    });
});

describe('filters API calls', () => {
    beforeEach(() => {
        vi.restoreAllMocks();
    });

    describe('loadFilters', () => {
        it('calls the endpoint with its parameters and returns the data', async () => {
            // Test Data
            const response = { success: true };
            vi.spyOn(apiClient, 'GET').mockResolvedValueOnce({
                data: response,
                error: undefined,
                response: new Response(),
            } as never);

            // Test Action
            const result = await loadFilters(10, 3);

            // Expected Result
            expect(result).toEqual(response);
            expect(apiClient.GET).toHaveBeenCalledWith(
                '/taxsystem/api/owner/{owner_id}/filter-set/{filterset_pk}/view/filter/',
                { params: { path: { owner_id: 10, filterset_pk: 3 } } },
            );
        });
    });
});

type Method = 'GET' | 'POST';

/** Every call of `Api/calls/filters.ts`: [name, HTTP method, call, fixed text]. */
const calls: [string, Method, () => Promise<unknown>, string][] = [
    ['loadFilterSets', 'GET', () => loadFilterSets(1), 'Failed to load filter sets'],
    ['loadFilters', 'GET', () => loadFilters(1, 2), 'Failed to load filters'],
    ['deleteFilter', 'POST', () => deleteFilter(1, 2), 'Failed to delete filter'],
    ['deleteFilterSet', 'POST', () => deleteFilterSet(1, 2), 'Failed to delete filter set'],
    ['switchFilterSet', 'POST', () => switchFilterSet(1, 2), 'Failed to switch filter set'],
    ['createFilterSet', 'POST', () => createFilterSet(1, {} as never), 'Failed to create filter set'],
    ['createFilter', 'POST', () => createFilter(1, {} as never), 'Failed to create filter'],
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
