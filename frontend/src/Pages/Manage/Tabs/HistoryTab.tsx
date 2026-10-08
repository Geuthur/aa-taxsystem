// React
import { useMemo } from "react";

// Third Party
import { useQuery } from "@tanstack/react-query";
import { History } from "lucide-react";
import { Card } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// AA TaxSystem
import { loadAdminLogs } from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";
import { BaseTable } from "@/Components/Base/BaseTable";
import { getHistoryColumns } from "@/Components/Tables";

interface HistoryTabProps {
  ownerId: number;
}

export function HistoryTab({ ownerId }: HistoryTabProps) {
  const { t } = useTranslation();

  const { data: logs, isLoading, isError } = useQuery({
    queryKey: queryKeys.AdminLogs(ownerId),
    queryFn: () => loadAdminLogs(ownerId),
  });

  const columns = useMemo(() => getHistoryColumns({ t }), [t]);

  return (
    <div className="mt-3">
      <Card className="bg-dark border-secondary">
        <Card.Header className="d-flex align-items-center justify-content-between border-secondary">
          <h5 className="mb-0 d-flex align-items-center gap-2">
            <History size={18} className="text-warning" />
            {t("Admin History")}
          </h5>
        </Card.Header>
        <Card.Body>
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
