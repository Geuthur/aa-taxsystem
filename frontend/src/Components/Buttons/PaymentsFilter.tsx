// AA TaxSystem
import { ButtonGroupFilter } from "@/Components/Buttons/ButtonGroupFilter";

export interface PaymentsFilterProps {
  statusFilter: string;
  setStatusFilter: (statusFilter: string) => void;
  t: (key: string) => string;
}

export function PaymentsFilter({ statusFilter, setStatusFilter, t }: PaymentsFilterProps) {
  const options = [
    { value: "all", label: t("All"), activeVariant: "aa-btn-primary" },
    { value: "pending", label: t("Pending"), activeVariant: "aa-btn-warning" },
    { value: "approved", label: t("Approved"), activeVariant: "aa-btn-success" },
    { value: "rejected", label: t("Rejected"), activeVariant: "aa-btn-danger" },
  ];

  return (
    <ButtonGroupFilter
      value={statusFilter}
      onChange={setStatusFilter}
      options={options}
      ariaLabel="Filter payments by status"
    />
  );
}

export default PaymentsFilter;

