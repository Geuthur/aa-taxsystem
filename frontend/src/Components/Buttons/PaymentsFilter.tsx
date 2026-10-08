// Third Party
import { Button } from "react-bootstrap";

export interface PaymentsFilterProps {
    statusFilter: string;
    setStatusFilter: (statusFilter: string) => void;
    t: (key: string) => string;
}

export function PaymentsFilter({ statusFilter, setStatusFilter, t }: PaymentsFilterProps) {
    return (
        <>
            <Button
                className={statusFilter === "all" ? "aa-btn aa-btn-primary" : "aa-btn aa-btn-secondary"}
                onClick={() => setStatusFilter("all")}
            >
                {t("All")}
            </Button>
            <Button
                className={statusFilter === "pending" ? "aa-btn aa-btn-warning" : "aa-btn aa-btn-secondary"}
                onClick={() => setStatusFilter("pending")}
            >
                {t("Pending")}
            </Button>
            <Button
                className={statusFilter === "approved" ? "aa-btn aa-btn-success" : "aa-btn aa-btn-secondary"}
                onClick={() => setStatusFilter("approved")}
            >
                {t("Approved")}
            </Button>
            <Button
                className={statusFilter === "rejected" ? "aa-btn aa-btn-danger" : "aa-btn aa-btn-secondary"}
                onClick={() => setStatusFilter("rejected")}
            >
                {t("Rejected")}
            </Button>
        </>
    );
}
