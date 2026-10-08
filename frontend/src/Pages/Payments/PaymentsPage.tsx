// React
import { useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

// Third Party
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, CreditCard, Search } from "lucide-react";
import { Badge, Button, Form, InputGroup, Spinner } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// AA TaxSystem
import { loadPaymentDetails, loadPayments } from "@/Api/ApiCalls";
import type { components } from "@/Api/OpenApi";
import { queryKeys } from "@/Api/query";
import BaseSectionHeader from "@/Components/Base/BaseHeader";
import { BaseModal, ModalSize } from "@/Components/Base/BaseModal";
import { BaseTable } from "@/Components/Base/BaseTable";
import { PaymentsFilter } from "@/Components/Buttons/PaymentsFilter";
import {
  PaymentActionButtons,
  PaymentActionModals,
} from "@/Components/Payments";
import { getPaymentColumns } from "@/Components/Tables";
import { usePaymentActions } from "@/Hooks/usePaymentActions";
import { useStatusFilterState, useTableSearchState } from "@/Hooks/useTaxsystemState";
import { formatNumber } from "@/Utils";

type PaymentRow = components["schemas"]["PaymentCorporationSchema"];

export function PaymentsPage() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const { ownerId } = useParams<{ ownerId: string }>();
  const numericOwnerId = Number(ownerId || 0);

  const [search, setSearch] = useTableSearchState("paymentSearch");
  const [statusFilter, setStatusFilter] = useStatusFilterState("paymentStatus");

  // Details Modal state
  const [detailsPaymentId, setDetailsPaymentId] = useState<number | null>(null);

  const { data: payments, isLoading, isError } = useQuery({
    queryKey: queryKeys.Payments(numericOwnerId),
    queryFn: () => loadPayments(numericOwnerId),
    enabled: numericOwnerId > 0,
  });

  const { data: paymentDetails, isLoading: detailsLoading } = useQuery({
    queryKey: queryKeys.PaymentDetails(numericOwnerId, detailsPaymentId || 0),
    queryFn: () => loadPaymentDetails(numericOwnerId, detailsPaymentId!),
    enabled: Boolean(detailsPaymentId && detailsPaymentId > 0),
  });

  const {
    approve,
    undo,
    rejectingPayment,
    setRejectingPayment,
    rejectComment,
    setRejectComment,
    confirmReject,
    deletingPayment,
    setDeletingPayment,
    deleteComment,
    setDeleteComment,
    confirmDelete,
    isPending,
  } = usePaymentActions({
    ownerId: numericOwnerId,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.Payments(numericOwnerId) });
    },
  });

  const filteredPayments = useMemo(() => {
    if (!payments) return [];
    return payments.filter((p) => {
      const matchesSearch =
        !search ||
        p.character?.character_name?.toLowerCase().includes(search.toLowerCase()) ||
        p.reason?.toLowerCase().includes(search.toLowerCase());
      const statusCode = (
        p.request_status?.code ||
        p.request_status?.status ||
        ""
      ).toLowerCase();
      const matchesStatus = statusFilter === "all" || statusCode === statusFilter.toLowerCase();
      return matchesSearch && matchesStatus;
    });
  }, [payments, search, statusFilter]);

  const columns = useMemo(
    () =>
      getPaymentColumns<PaymentRow>({
        t,
        showCharacter: true,
        renderActions: (p) => (
          <PaymentActionButtons
            payment={p}
            onViewDetails={setDetailsPaymentId}
            onApprove={approve}
            onReject={setRejectingPayment}
            onUndo={undo}
            onDelete={setDeletingPayment}
            isPending={isPending}
          />
        ),
      }),
    [t, approve, setRejectingPayment, undo, setDeletingPayment, isPending],
  );

  return (
    <main>
      <BaseSectionHeader name={t("Payments Management")}>
        <Link to="/" className="aa-btn aa-btn-sm aa-btn-secondary d-flex align-items-center gap-1">
          <ArrowLeft size={14} />
          {t("Overview")}
        </Link>
      </BaseSectionHeader>

      <div className="mt-3 p-3 aa-panel rounded">
        <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-3">
          <div className="d-flex flex-wrap align-items-center gap-2">
            <InputGroup style={{ maxWidth: 360 }}>
              <InputGroup.Text className="bg-dark border-secondary text-secondary">
                <Search size={16} />
              </InputGroup.Text>
              <Form.Control
                type="text"
                placeholder={t("Filter by character or reason...")}
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="bg-dark text-light border-secondary"
              />
            </InputGroup>

            <PaymentsFilter statusFilter={statusFilter} setStatusFilter={setStatusFilter} t={t} />
          </div>
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

      <PaymentActionModals
        rejectingPayment={rejectingPayment}
        rejectComment={rejectComment}
        onRejectCommentChange={setRejectComment}
        onCancelReject={() => setRejectingPayment(null)}
        onConfirmReject={confirmReject}
        deletingPayment={deletingPayment}
        deleteComment={deleteComment}
        onDeleteCommentChange={setDeleteComment}
        onCancelDelete={() => setDeletingPayment(null)}
        onConfirmDelete={confirmDelete}
        isPending={isPending}
      />

      {/* Details & History Modal */}
      {detailsPaymentId && (
        <BaseModal
          show={!!detailsPaymentId}
          onHide={() => setDetailsPaymentId(null)}
          size={ModalSize.large}
          title={
            <div className="h5 d-flex align-items-center gap-2 mb-0">
              <CreditCard size={18} className="text-info" />
              {t("Payment Details & History")}
            </div>
          }
          footer={
            <Button variant="secondary" onClick={() => setDetailsPaymentId(null)}>
              {t("Close")}
            </Button>
          }
        >
          {detailsLoading ? (
            <div className="text-center py-4">
              <Spinner animation="border" variant="info" />
            </div>
          ) : paymentDetails ? (
            <div>
              <div className="d-flex justify-content-between align-items-center p-3 rounded bg-secondary bg-opacity-25 mb-3">
                <div>
                  <h6 className="mb-1 text-light">{paymentDetails.account?.character?.character_name}</h6>
                  <div className="text-muted small">
                    {t("Payment Pool")}: {formatNumber(Number(paymentDetails.account?.payment_pool || 0))}
                  </div>
                </div>
                <div className="text-end">
                  <h5 className="mb-1 text-info fw-bold">
                    {formatNumber(Number(paymentDetails.payment?.amount || 0))}
                  </h5>
                  <Badge bg="secondary">{paymentDetails.payment?.request_status?.status}</Badge>
                </div>
              </div>

              <h6 className="mt-4 mb-2">{t("Audit History")}</h6>
              <div className="bg-secondary bg-opacity-25 border border-secondary rounded p-2">
                {paymentDetails.payment_histories?.length ? (
                  paymentDetails.payment_histories.map((h) => (
                    <div key={h.log_id} className="d-flex justify-content-between border-bottom border-secondary py-2 small">
                      <div>
                        <span className="fw-semibold text-light">{h.reviser}</span>: {h.action}
                        {h.comment && <div className="text-muted fst-italic">"{h.comment}"</div>}
                      </div>
                      <span className="text-muted">{h.date}</span>
                    </div>
                  ))
                ) : (
                  <div className="text-muted small text-center py-2">{t("No audit history for this payment.")}</div>
                )}
              </div>
            </div>
          ) : null}
        </BaseModal>
      )}
    </main>
  );
}

export default PaymentsPage;
