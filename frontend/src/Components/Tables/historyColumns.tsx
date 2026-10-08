// Third Party
import { type ColumnDef } from "@tanstack/react-table";
import type { TFunction } from "i18next";
import { Badge } from "react-bootstrap";

// AA TaxSystem
import type { components } from "@/Api/OpenApi";

export type AdminLogRow = components["schemas"]["AdminHistorySchema"];

export interface HistoryColumnsOptions {
  t: TFunction;
}

export function getHistoryColumns({ t }: HistoryColumnsOptions): ColumnDef<AdminLogRow>[] {
  return [
    {
      id: "date",
      header: t("Date"),
      accessorKey: "date",
      cell: ({ getValue }) => (
        <span className="small text-muted">{String(getValue() || "")}</span>
      ),
    },
    {
      id: "user_name",
      header: t("Admin"),
      accessorKey: "user_name",
      cell: ({ getValue }) => (
        <span className="fw-semibold">{String(getValue() || "")}</span>
      ),
    },
    {
      id: "target",
      header: t("Target"),
      accessorKey: "target",
      cell: ({ getValue }) => (
        <Badge bg="secondary">{String(getValue() || "")}</Badge>
      ),
    },
    {
      id: "action",
      header: t("Action"),
      accessorKey: "action",
      cell: ({ row }) => {
        const raw = String(row.original.action ?? "").toLowerCase().trim();
        const label = String(row.original.action_display || row.original.action || "");

        if (raw.includes("deleted")) {
          return <Badge bg="danger">{label}</Badge>;
        }
        if (raw.includes("added")) {
          return <Badge bg="success">{label}</Badge>;
        }
        if (raw.includes("changed")) {
          return (
            <Badge bg="warning" className="text-dark">
              {label}
            </Badge>
          );
        }
        return <Badge bg="secondary">{label}</Badge>;
      },
    },
    {
      id: "comment",
      header: t("Comment"),
      accessorKey: "comment",
    },
  ];
}
