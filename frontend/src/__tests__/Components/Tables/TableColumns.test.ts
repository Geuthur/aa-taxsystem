// Third Party
import type { TFunction } from 'i18next';
import { describe, expect, it } from 'vitest';

// AA TaxSystem
import {getExampleColumns} from '@/Components/Tables/TableColumns';

describe('TableColumns definitions', () => {
    const mockT = ((key: string) => `trans_${key}`) as unknown as TFunction;

    describe('getExampleColumns', () => {
        it('returns 6 column definitions for snapshot ore list', () => {
            const columns = getExampleColumns(mockT);
            expect(columns).toHaveLength(6);

            const headers = columns.map((col) =>
                typeof col.header === 'string' ? col.header : undefined,
            );
            expect(headers).toEqual([
                'trans_Ore',
                'trans_Units Left',
                'trans_Volume Left (m³)',
                'trans_Price (ISK/m³)',
                'trans_Price Compressed',
                'trans_Income Compressed (ISK/h)',
            ]);
        });

        it('has cell formatter for numeric fields', () => {
            const columns = getExampleColumns(mockT);
            const unitsCol = columns.find((col) => (col as { accessorKey?: string }).accessorKey === 'units');
            expect(unitsCol).toBeDefined();
            expect(typeof unitsCol?.cell).toBe('function');
        });
    });
});
