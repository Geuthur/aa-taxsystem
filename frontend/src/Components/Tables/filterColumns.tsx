// Third Party
import { type ColumnDef } from "@tanstack/react-table";
import type { TFunction } from "i18next";
import { ArrowRight, Trash2 } from "lucide-react";
import { Badge, Button } from "react-bootstrap";

// AA TaxSystem
import type { components } from "@/Api/OpenApi";

export type FilterSetRow = components["schemas"]["FilterSetModelSchema"];
export type FilterRow = components["schemas"]["FilterModelSchema"];

export interface FilterSetColumnsOptions {
  t: TFunction;
  activeSetId?: number | null;
  onSelect: (id: number) => void;
  onDelete: (id: number) => void;
}

export function getFilterSetColumns({
  t,
  activeSetId,
  onSelect,
  onDelete,
}: FilterSetColumnsOptions): ColumnDef<FilterSetRow>[] {
  return [
    {
      id: "name",
      header: t("Name"),
      accessorKey: "name",
      cell: ({ row }) => (
        <div className="d-flex align-items-center gap-2">
          {row.original.id === activeSetId && <ArrowRight />}
          <Button
            variant="link"
            className="fw-semibold text-decoration-none"
            onClick={() => row.original.id && onSelect(row.original.id)}
          >
            <span
              className={
                row.original.id === activeSetId ? "text-primary" : "text-light"
              }
            >
              {row.original.name}
            </span>
          </Button>
        </div>
      ),
    },
    {
      id: "description",
      header: t("Description"),
      accessorKey: "description",
    },
    {
      id: "enabled",
      header: t("Status"),
      accessorKey: "enabled",
      cell: ({ getValue }) =>
        getValue() ? (
          <Badge bg="success">{t("Enabled")}</Badge>
        ) : (
          <Badge bg="secondary">{t("Disabled")}</Badge>
        ),
    },
    {
      id: "actions",
      header: t("Actions"),
      cell: ({ row }) =>
        row.original.id ? (
          <Button
            className="aa-btn aa-btn-sm aa-btn-danger"
            onClick={() => onDelete(row.original.id!)}
          >
            <Trash2 size={12} />
            {t("Delete")}
          </Button>
        ) : null,
    },
  ];
}

export interface FilterRuleColumnsOptions {
  t: TFunction;
  filterTypeLabels: Record<string, string>;
  matchTypeLabels: Record<string, string>;
  onDelete: (id: number) => void;
}

export function getFilterRuleColumns({
  t,
  filterTypeLabels,
  matchTypeLabels,
  onDelete,
}: FilterRuleColumnsOptions): ColumnDef<FilterRow>[] {
  return [
    {
      id: "filter_set",
      header: t("Filter Set"),
      accessorFn: (row) => row.filter_set?.name,
    },
    {
      id: "filter_type",
      header: t("Type"),
      accessorKey: "filter_type",
      cell: ({ row }) => row.original.filter_type_display,
      meta: { filterOptionLabel: (v: string) => filterTypeLabels[v] ?? v },
    },
    {
      id: "match_type",
      header: t("Match"),
      accessorKey: "match_type",
      cell: ({ row }) => row.original.match_type_display,
      meta: { filterOptionLabel: (v: string) => matchTypeLabels[v] ?? v },
    },
    {
      id: "value",
      header: t("Value"),
      accessorKey: "value",
      cell: ({ row }) => row.original.value_display,
    },
    {
      id: "actions",
      header: t("Actions"),
      cell: ({ row }) =>
        row.original.id ? (
          <Button
            className="aa-btn aa-btn-sm aa-btn-danger"
            onClick={() => onDelete(row.original.id!)}
          >
            <Trash2 size={12} />
            {t("Delete")}
          </Button>
        ) : null,
    },
  ];
}
