// Third Party
import { createColumnHelper } from "@tanstack/react-table";
import type { ColumnDef } from "@tanstack/react-table";
import type { TFunction } from "i18next";

// AA TaxSystem
import { formatNumber } from "@/Components/Base/BaseTable/tableHelper";

type ExampleRow = {
    name: string;
    units: number;
    volume_m3: number;
    price_isk: number;
    price_compressed: number;
    income_cmp_per_h: number;
};

export function getExampleColumns(
    t: TFunction,
): ColumnDef<ExampleRow, unknown>[] {
    const columnHelper = createColumnHelper<ExampleRow>();

    // Translations for tooltips and titles
    const tOre = t("Ore");
    const tUnitsLeft = t("Units Left");
    const tVolumeLeft = t("Volume Left (m³)");
    const tPriceISK = t("Price (ISK/m³)");
    const tPriceCompressed = t("Price Compressed");
    const tIncomeCompressed = t("Income Compressed (ISK/h)");

    return [
        columnHelper.accessor('name', {
            header: tOre,
        }),
        columnHelper.accessor('units', {
            header: tUnitsLeft,
            cell: ({ getValue }) => formatNumber(Number(getValue())),
        }),
        columnHelper.accessor('volume_m3', {
            header: tVolumeLeft,
            cell: ({ getValue }) => formatNumber(Number(getValue())),
        }),
        columnHelper.accessor('price_isk', {
            header: tPriceISK,
            cell: ({ getValue }) => formatNumber(Number(getValue())),
        }),
        columnHelper.accessor('price_compressed', {
            header: tPriceCompressed,
            cell: ({ getValue }) => formatNumber(Number(getValue())),
        }),
        columnHelper.accessor('income_cmp_per_h', {
            header: tIncomeCompressed,
            cell: ({ getValue }) => formatNumber(Number(getValue())),
        }),
    ] as ColumnDef<ExampleRow, unknown>[];
}
