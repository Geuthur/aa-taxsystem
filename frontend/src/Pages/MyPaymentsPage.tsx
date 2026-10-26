// React
import { useMemo } from "react";
import { Link, useParams } from "react-router-dom";

// Third Party
import { ArrowLeft } from "lucide-react";
import { Card } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// AA TaxSystem
import type { components } from "@/Api/OpenApi";
import BaseSectionHeader from "@/Components/Base/BaseHeader";
import { BaseTable } from "@/Components/Base/BaseTable";
import { SearchInput } from "@/Components/Base/SearchInput";
import { useMyPayments } from "@/Components/Payments/Hooks";
import { getPaymentColumns } from "@/Components/Tables";
import { useTableSearchState } from "@/Hooks/useTaxsystemState";

type MyPaymentRow = components["schemas"]["PaymentSchema"];

export function MyPaymentsPage() {
  const { t } = useTranslation();
  const { ownerId } = useParams<{ ownerId: string }>();
  const numericOwnerId = Number(ownerId || 0);

  const [search, setSearch] = useTableSearchState("myPaymentSearch");

  const { data: payments, isLoading, isError } = useMyPayments(numericOwnerId);

  const filteredPayments = useMemo(() => {
    if (!payments) return [];
    if (!search) return payments;
    const q = search.toLowerCase();
    return payments.filter(
      (p) =>
        p.reason?.toLowerCase().includes(q) ||
        p.division_name?.toLowerCase().includes(q),
    );
  }, [payments, search]);

  const columns = useMemo(
    () =>
      getPaymentColumns<MyPaymentRow>({
        t,
        showCharacter: false,
        showReviser: true,
      }),
    [t],
  );

  return (
    <Card className="border-0 bg-transparent">
      <BaseSectionHeader name={t("My Invoices & Payments")}>
        <Link to="/" className="btn btn-sm btn-secondary d-flex align-items-center gap-1">
          <ArrowLeft size={14} />
          {t("Overview")}
        </Link>
      </BaseSectionHeader>

      <div className="mt-3 p-3 aa-panel rounded">
        <div className="d-flex justify-content-between align-items-center mb-3">
          <SearchInput
            value={search}
            onChange={setSearch}
            placeholder={t("Filter by division or reason…")}
          />
        </div>

        <BaseTable
          data={filteredPayments}
          columns={columns}
          isFetching={isLoading}
          isError={isError}
          emptyText={t("No payments found.")}
          variant="light"
        />
      </div>
    </Card>
  );
}

export default MyPaymentsPage;
