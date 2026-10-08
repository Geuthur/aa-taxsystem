// React
import { useMemo } from "react";

// Third Party
import { useQuery } from "@tanstack/react-query";
import { type ColumnDef } from "@tanstack/react-table";
import { History } from "lucide-react";
import { Badge, Card } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// AA TaxSystem
import { loadAdminLogs } from "@/Api/ApiCalls";
import type { components } from "@/Api/OpenApi";
import { queryKeys } from "@/Api/query";
import { BaseTable } from "@/Components/Base/BaseTable";

interface HistoryTabProps {
  ownerId: number;
}

type AdminLogRow = components["schemas"]["AdminHistorySchema"];

export function HistoryTab({ ownerId }: HistoryTabProps) {
  const { t } = useTranslation();

  const { data: logs, isLoading, isError } = useQuery({
    queryKey: queryKeys.AdminLogs(ownerId),
    queryFn: () => loadAdminLogs(ownerId),
  });

  const columns = useMemo<ColumnDef<AdminLogRow>[]>(
    () => [
      {
        id: "date",
        header: t("Date"),
        accessorKey: "date",
        cell: ({ getValue }) => <span className="small text-muted">{String(getValue() || "")}</span>,
      },
      {
        id: "user_name",
        header: t("Admin"),
        accessorKey: "user_name",
        cell: ({ getValue }) => <span className="fw-semibold">{String(getValue() || "")}</span>,
      },
      {
        id: "target",
        header: t("Target"),
        accessorKey: "target",
        cell: ({ getValue }) => <Badge bg="secondary">{String(getValue() || "")}</Badge>,
      },
      {
        id: "action",
        header: t("Action"),
        accessorKey: "action",
        cell: ({ row }) => {
          const raw = (row.original.action ?? "").toLowerCase().trim();
          const label = row.original.action_display || row.original.action || "";

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
    ],
    [t],
  );

  return (
    <div className="mt-3">
      <Card className="bg-dark border-secondary">
        <Card.Header className="d-flex align-items-center justify-content-between border-secondary">
          <h5 className="mb-0 d-flex align-items-center gap-2">
            <History size={18} className="text-warning" />
            {t("Admin History")}
          </h5>
        </Card.Header>
        <Card.Body className="p-0">
          <BaseTable
            data={logs || []}
            columns={columns}
            isFetching={isLoading}
            isError={isError}
            emptyText={t("No admin logs found.")}
          />
        </Card.Body>
      </Card>
    </div>
  );
}

export default HistoryTab;
