// Third Party
import { FilterButtonGroup } from "aa-geuthur-react";

export interface PaymentsFilterProps {
  statusFilter: string;
  setStatusFilter: (statusFilter: string) => void;
  t: (key: string) => string;
}

export function PaymentsFilter({ statusFilter, setStatusFilter, t }: PaymentsFilterProps) {
  const options = [
    { value: "all", label: t("All") },
    { value: "pending", label: t("Pending") },
    { value: "needs_approval", label: t("Needs Approval") },
    { value: "approved", label: t("Approved") },
    { value: "rejected", label: t("Rejected") },
  ];

  return (
    <FilterButtonGroup
      value={statusFilter}
      onChange={setStatusFilter}
      options={options}
      ariaLabel="Filter payments by status"
    />
  );
}

export default PaymentsFilter;

