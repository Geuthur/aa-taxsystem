// Third Party
import { type ColumnDef } from "@tanstack/react-table";
import type { TFunction } from "i18next";
import { Trash2 } from "lucide-react";
import { Badge, Button } from "react-bootstrap";

// AA TaxSystem
import type { components } from "@/Api/OpenApi";

export type GroupManagementRow = components["schemas"]["GroupManagementSchema"];

export interface GroupColumnsOptions {
  t: TFunction;
  onDelete: (group: GroupManagementRow) => void;
}

export function getGroupColumns({
  t,
  onDelete,
}: GroupColumnsOptions): ColumnDef<GroupManagementRow>[] {
  return [
    {
      id: "name",
      header: t("Name"),
      accessorKey: "name",
      cell: ({ getValue }) => <span className="fw-semibold">{String(getValue() || "")}</span>,
    },
    {
      id: "groups",
      header: t("Assigned Groups"),
      cell: ({ row }) => (
        <div className="d-flex flex-wrap gap-1">
          {row.original.groups?.map((g) => (
            <Badge key={g.id} bg="primary">
              {g.name}
            </Badge>
          )) || <span className="text-muted">—</span>}
        </div>
      ),
    },
    {
      id: "actions",
      header: t("Actions"),
      cell: ({ row }) =>
        row.original.id ? (
          <Button
            className="aa-btn aa-btn-sm aa-btn-danger"
            onClick={() => onDelete(row.original)}
          >
            <Trash2 size={12} />
            {t("Delete")}
          </Button>
        ) : null,
    },
  ];
}
