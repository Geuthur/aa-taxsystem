// Third Party
import { Button } from "react-bootstrap";

export interface PaymentsFilterProps {
  statusFilter: string;
  setStatusFilter: (statusFilter: string) => void;
  t: (key: string) => string;
}

export function PaymentsFilter({ statusFilter, setStatusFilter, t }: PaymentsFilterProps) {
  return (
    <div className="btn-group" role="group">
      <Button
        className={`aa-btn aa-btn-sm ${statusFilter === "all" ? "aa-btn-primary" : "aa-btn-secondary"}`}
        onClick={() => setStatusFilter("all")}
      >
        {t("All")}
      </Button>
      <Button
        className={`aa-btn aa-btn-sm ${statusFilter === "pending" ? "aa-btn-warning" : "aa-btn-secondary"}`}
        onClick={() => setStatusFilter("pending")}
      >
        {t("Pending")}
      </Button>
      <Button
        className={`aa-btn aa-btn-sm ${statusFilter === "approved" ? "aa-btn-success" : "aa-btn-secondary"}`}
        onClick={() => setStatusFilter("approved")}
      >
        {t("Approved")}
      </Button>
      <Button
        className={`aa-btn aa-btn-sm ${statusFilter === "rejected" ? "aa-btn-danger" : "aa-btn-secondary"}`}
        onClick={() => setStatusFilter("rejected")}
      >
        {t("Rejected")}
      </Button>
    </div>
  );
}
