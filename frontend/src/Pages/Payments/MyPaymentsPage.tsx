// React
import { useMemo } from "react";
import { Link, useParams } from "react-router-dom";

// Third Party
import { useQuery } from "@tanstack/react-query";
import { ArrowLeft, Search } from "lucide-react";
import { Form, InputGroup } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// AA TaxSystem
import { loadMyPayments } from "@/Api/ApiCalls";
import type { components } from "@/Api/OpenApi";
import { queryKeys } from "@/Api/query";
import BaseSectionHeader from "@/Components/Base/BaseHeader";
import { BaseTable } from "@/Components/Base/BaseTable";
import { getPaymentColumns } from "@/Components/Tables";
import { useTableSearchState } from "@/Hooks/useTaxsystemState";

type MyPaymentRow = components["schemas"]["PaymentSchema"];

export function MyPaymentsPage() {
  const { t } = useTranslation();
  const { ownerId } = useParams<{ ownerId: string }>();
  const numericOwnerId = Number(ownerId || 0);

  const [search, setSearch] = useTableSearchState("myPaymentSearch");

  const { data: payments, isLoading, isError } = useQuery({
    queryKey: queryKeys.MyPayments(numericOwnerId),
    queryFn: () => loadMyPayments(numericOwnerId),
    enabled: numericOwnerId > 0,
  });

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
    <main>
      <BaseSectionHeader name={t("My Invoices & Payments")}>
        <Link to="/" className="aa-btn aa-btn-sm aa-btn-secondary d-flex align-items-center gap-1">
          <ArrowLeft size={14} />
          {t("Overview")}
        </Link>
      </BaseSectionHeader>

      <div className="mt-3 p-3 aa-panel rounded">
        <div className="d-flex justify-content-between align-items-center mb-3">
          <InputGroup style={{ maxWidth: 360 }}>
            <InputGroup.Text className="bg-dark border-secondary text-secondary">
              <Search size={16} />
            </InputGroup.Text>
            <Form.Control
              type="text"
              placeholder={t("Filter by division or reason...")}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="bg-dark text-light border-secondary"
            />
          </InputGroup>
        </div>

        <BaseTable
          data={filteredPayments}
          columns={columns}
          isFetching={isLoading}
          isError={isError}
          emptyText={t("No payments found.")}
          variant="vowra-light"
        />
      </div>
    </main>
  );
}

export default MyPaymentsPage;
