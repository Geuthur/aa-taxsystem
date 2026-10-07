// Third Party
import { describe, expect, it } from 'vitest';

// AA TaxSystem
import { queryKeys } from '@/Api/query';

describe('queryKeys', () => {
    it('provides static query keys', () => {
        expect(queryKeys.Menu).toEqual(['Menu']);
        expect(queryKeys.User).toEqual(['User']);
    });
});
