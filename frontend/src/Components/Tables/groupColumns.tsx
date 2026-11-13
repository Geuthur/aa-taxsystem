// Third Party
import { renderTooltip } from "aa-geuthur-react";
import type { BaseColumnDef } from "aa-geuthur-react";
import type { TFunction } from "i18next";
import { Trash2 } from "lucide-react";
import { Badge, Button, ButtonGroup } from "react-bootstrap";

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
}: GroupColumnsOptions): BaseColumnDef<GroupManagementRow>[] {
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
          <ButtonGroup size="sm">
            {renderTooltip(
              t("Delete"),
              <Button
                variant="danger"
                aria-label={t("Delete")}
                onClick={() => onDelete(row.original)}
              >
                <Trash2 size={14} />
              </Button>,
            )}
          </ButtonGroup>
        ) : null,
    },
  ];
}
