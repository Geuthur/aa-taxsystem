// React
import { useMemo, useState } from "react";
import { Link, useParams } from "react-router-dom";

// Third Party
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { type ColumnDef } from "@tanstack/react-table";
import {
  ArrowLeft,
  Check,
  CreditCard,
  Eye,
  RotateCcw,
  Search,
  Trash2,
  X,
} from "lucide-react";
import { Badge, Button, Form, InputGroup, Spinner } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// AA TaxSystem
import {
  acceptPayment,
  deletePayment,
  loadPaymentDetails,
  loadPayments,
  rejectPayment,
  undoPayment,
} from "@/Api/ApiCalls";
import type { components } from "@/Api/OpenApi";
import { queryKeys } from "@/Api/query";
import BaseSectionHeader from "@/Components/Base/BaseHeader";
import { BaseModal, ModalSize } from "@/Components/Base/BaseModal";
import { BaseTable } from "@/Components/Base/BaseTable";
import { useStatusFilterState, useTableSearchState } from "@/Hooks/useTaxsystemState";
import { formatNumber } from "@/Utils";
import { PaymentsFilter } from "@/Components/Buttons/PaymentsFilter";

type PaymentRow = components["schemas"]["PaymentCorporationSchema"];

export function PaymentsPage() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const { ownerId } = useParams<{ ownerId: string }>();
  const numericOwnerId = Number(ownerId || 0);

  const [search, setSearch] = useTableSearchState("paymentSearch");
  const [statusFilter, setStatusFilter] = useStatusFilterState("paymentStatus");

  // Reject / Undo Modal states
  const [rejectingPayment, setRejectingPayment] = useState<PaymentRow | null>(null);
  const [rejectComment, setRejectComment] = useState("");

  // Delete Modal states
  const [deletingPayment, setDeletingPayment] = useState<PaymentRow | null>(null);
  const [deleteComment, setDeleteComment] = useState("");

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

  const acceptMutation = useMutation({
    mutationFn: (paymentPk: number) => acceptPayment(numericOwnerId, paymentPk),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.Payments(numericOwnerId) });
    },
  });

  const rejectMutation = useMutation({
    mutationFn: ({ paymentPk, comment }: { paymentPk: number; comment?: string }) =>
      rejectPayment(numericOwnerId, paymentPk, comment),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.Payments(numericOwnerId) });
      setRejectingPayment(null);
      setRejectComment("");
    },
  });

  const undoMutation = useMutation({
    mutationFn: (paymentPk: number) => undoPayment(numericOwnerId, paymentPk),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.Payments(numericOwnerId) });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: ({ paymentPk, comment }: { paymentPk: number; comment?: string }) =>
      deletePayment(numericOwnerId, paymentPk, comment),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.Payments(numericOwnerId) });
      setDeletingPayment(null);
      setDeleteComment("");
    },
  });

  const filteredPayments = useMemo(() => {
    if (!payments) return [];
    return payments.filter((p) => {
      const matchesSearch =
        !search ||
        p.character?.character_name?.toLowerCase().includes(search.toLowerCase()) ||
        p.reason?.toLowerCase().includes(search.toLowerCase());
      const statusText = p.request_status?.status?.toLowerCase() || "";
      const matchesStatus =
        statusFilter === "all" ||
        statusText.includes(statusFilter.toLowerCase());
      return matchesSearch && matchesStatus;
    });
  }, [payments, search, statusFilter]);

  const columns = useMemo<ColumnDef<PaymentRow>[]>(
    () => [
      {
        id: "character",
        header: t("Character", "Character"),
        accessorFn: (row) => row.character?.character_name,
        cell: ({ row }) => (
          <div className="d-flex align-items-center gap-2">
            {row.original.character?.character_portrait && (
              <img
                src={row.original.character.character_portrait}
                alt={row.original.character.character_name}
                width={32}
                height={32}
                className="rounded-circle"
              />
            )}
            <span className="fw-semibold">{row.original.character?.character_name}</span>
          </div>
        ),
      },
      {
        id: "date",
        header: t("Date", "Date"),
        accessorKey: "date",
        cell: ({ getValue }) => <span className="small text-muted">{String(getValue() || "")}</span>,
      },
      {
        id: "amount",
        header: t("Amount", "Amount"),
        accessorKey: "amount",
        cell: ({ getValue }) => {
          const val = Number(getValue() || 0);
          return <span className="fw-mono text-light">{formatNumber(val)}</span>;
        },
      },
      {
        id: "division",
        header: t("Division", "Division"),
        accessorKey: "division_name",
      },
      {
        id: "status",
        header: t("Status", "Status"),
        cell: ({ row }) => {
          const s = row.original.request_status;
          return (
            <Badge bg={s?.color === "green" ? "success" : s?.color === "red" ? "danger" : "warning"}>
              {s?.status}
            </Badge>
          );
        },
      },
      {
        id: "reason",
        header: t("Reason", "Reason"),
        accessorKey: "reason",
      },
      {
        id: "actions",
        header: t("Actions", "Actions"),
        cell: ({ row }) => {
          const p = row.original;
          const statusCode = p.request_status?.code?.toLowerCase() || "";
          const isPending =
            p.can_approve ??
            (statusCode === "pending" || statusCode === "needs_approval");
          const isProcessed =
            p.can_undo ??
            (statusCode === "approved" || statusCode === "rejected");
          const canDelete = Boolean(p.can_delete ?? p.is_custom);

          return (
            <div className="d-flex align-items-center gap-1">
              <Button
                variant="outline-info"
                size="sm"
                title={t("View Details", "View Details")}
                onClick={() => setDetailsPaymentId(p.payment_id)}
              >
                <Eye size={12} />
              </Button>
              {isPending && (
                <>
                  <Button
                    variant="outline-success"
                    size="sm"
                    title={t("Accept Payment", "Accept Payment")}
                    disabled={acceptMutation.isPending}
                    onClick={() => acceptMutation.mutate(p.payment_id)}
                  >
                    <Check size={12} />
                  </Button>
                  <Button
                    variant="outline-danger"
                    size="sm"
                    title={t("Reject Payment", "Reject Payment")}
                    onClick={() => setRejectingPayment(p)}
                  >
                    <X size={12} />
                  </Button>
                </>
              )}
              {isProcessed && (
                <Button
                  variant="outline-secondary"
                  size="sm"
                  title={t("Undo Payment", "Undo Payment")}
                  disabled={undoMutation.isPending}
                  onClick={() => undoMutation.mutate(p.payment_id)}
                >
                  <RotateCcw size={12} />
                </Button>
              )}
              {canDelete && (
                <Button
                  variant="outline-danger"
                  size="sm"
                  title={t("Delete Custom Payment", "Delete Custom Payment")}
                  disabled={deleteMutation.isPending}
                  onClick={() => {
                    setDeletingPayment(p);
                    setDeleteComment("");
                  }}
                >
                  <Trash2 size={12} />
                </Button>
              )}
            </div>
          );
        },
      },
    ],
    [t, acceptMutation, undoMutation, deleteMutation],
  );

  return (
    <main>
      <BaseSectionHeader name={t("Payments Management", "Payments Management")}>
        <Link to="/" className="aa-btn aa-btn-sm aa-btn-secondary d-flex align-items-center gap-1">
          <ArrowLeft size={14} />
          {t("Overview", "Overview")}
        </Link>
      </BaseSectionHeader>

      <div className="mt-3 p-3 aa-panel rounded">
        <div className="d-flex flex-wrap justify-content-between align-items-center gap-3 mb-3">
          <InputGroup style={{ maxWidth: 360 }}>
            <InputGroup.Text className="bg-dark border-secondary text-secondary">
              <Search size={16} />
            </InputGroup.Text>
            <Form.Control
              type="text"
              placeholder={t("Filter by character or reason...", "Filter by character or reason...")}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="bg-dark text-light border-secondary"
            />
          </InputGroup>

          <div className="d-flex gap-2">
            <PaymentsFilter statusFilter={statusFilter} setStatusFilter={setStatusFilter} t={t} />
          </div>
        </div>

        <BaseTable
          data={filteredPayments}
          columns={columns}
          isFetching={isLoading}
          isError={isError}
          emptyText={t("No payments found.", "No payments found.")}
        />
      </div>

      {/* Reject Payment Modal */}
      {rejectingPayment && (
        <BaseModal
          show={!!rejectingPayment}
          onHide={() => setRejectingPayment(null)}
          size={ModalSize.medium}
          title={
            <div className="h5 text-danger d-flex align-items-center gap-2 mb-0">
              <X size={18} />
              {t("Reject Payment", "Reject Payment")}
            </div>
          }
          footer={
            <>
              <Button variant="secondary" onClick={() => setRejectingPayment(null)}>
                {t("Cancel", "Cancel")}
              </Button>
              <Button
                variant="danger"
                disabled={rejectMutation.isPending}
                onClick={() =>
                  rejectMutation.mutate({
                    paymentPk: rejectingPayment.payment_id,
                    comment: rejectComment,
                  })
                }
              >
                {rejectMutation.isPending && <Spinner size="sm" animation="border" className="me-1" />}
                {t("Confirm Rejection", "Confirm Rejection")}
              </Button>
            </>
          }
        >
          <p>
            {t("Rejecting payment of", "Rejecting payment of")}{" "}
            <strong>{formatNumber(Number(rejectingPayment.amount || 0))}</strong>{" "}
            {t("from", "from")} <strong>{rejectingPayment.character?.character_name}</strong>.
          </p>
          <Form.Group className="mb-3">
            <Form.Label>{t("Rejection Reason / Comment", "Rejection Reason / Comment")}</Form.Label>
            <Form.Control
              as="textarea"
              rows={3}
              value={rejectComment}
              onChange={(e) => setRejectComment(e.target.value)}
              placeholder={t("Reason for rejecting payment...", "Reason for rejecting payment...")}
              className="bg-dark text-light border-secondary"
            />
          </Form.Group>
        </BaseModal>
      )}

      {/* Delete Custom Payment Modal */}
      {deletingPayment && (
        <BaseModal
          show={!!deletingPayment}
          onHide={() => setDeletingPayment(null)}
          size={ModalSize.medium}
          title={
            <div className="h5 d-flex align-items-center gap-2 text-danger mb-0">
              <Trash2 size={18} />
              {t("Delete Custom Payment", "Delete Custom Payment")}
            </div>
          }
          footer={
            <>
              <Button variant="secondary" onClick={() => setDeletingPayment(null)}>
                {t("Cancel", "Cancel")}
              </Button>
              <Button
                variant="danger"
                disabled={deleteMutation.isPending}
                onClick={() =>
                  deleteMutation.mutate({
                    paymentPk: deletingPayment.payment_id,
                    comment: deleteComment || "Deleted via TaxSystem",
                  })
                }
              >
                {deleteMutation.isPending && (
                  <Spinner size="sm" animation="border" className="me-1" />
                )}
                {t("Confirm Deletion", "Confirm Deletion")}
              </Button>
            </>
          }
        >
          <p>
            {t(
              "Are you sure you want to permanently delete this custom payment of",
              "Are you sure you want to permanently delete this custom payment of",
            )}{" "}
            <strong className="text-danger">
              {formatNumber(Number(deletingPayment.amount || 0))}
            </strong>{" "}
            {t("from", "from")} <strong>{deletingPayment.character?.character_name}</strong>?
          </p>
          {deletingPayment.request_status?.code === "approved" && (
            <div className="alert alert-warning small mb-3">
              {t(
                "This payment was already approved. Deleting it will automatically deduct this amount from the member's account deposit.",
                "This payment was already approved. Deleting it will automatically deduct this amount from the member's account deposit.",
              )}
            </div>
          )}
          <Form.Group className="mb-3">
            <Form.Label>{t("Deletion Reason / Comment", "Deletion Reason / Comment")}</Form.Label>
            <Form.Control
              as="textarea"
              rows={3}
              value={deleteComment}
              onChange={(e) => setDeleteComment(e.target.value)}
              placeholder={t(
                "Reason for deleting this custom payment...",
                "Reason for deleting this custom payment...",
              )}
              className="bg-dark text-light border-secondary"
            />
          </Form.Group>
        </BaseModal>
      )}

      {/* Details & History Modal */}
      {detailsPaymentId && (
        <BaseModal
          show={!!detailsPaymentId}
          onHide={() => setDetailsPaymentId(null)}
          size={ModalSize.large}
          title={
            <div className="h5 d-flex align-items-center gap-2 mb-0">
              <CreditCard size={18} className="text-info" />
              {t("Payment Details & History", "Payment Details & History")}
            </div>
          }
          footer={
            <Button variant="secondary" onClick={() => setDetailsPaymentId(null)}>
              {t("Close", "Close")}
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
                    {t("Payment Pool", "Payment Pool")}: {formatNumber(Number(paymentDetails.account?.payment_pool || 0))}
                  </div>
                </div>
                <div className="text-end">
                  <h5 className="mb-1 text-info fw-bold">
                    {formatNumber(Number(paymentDetails.payment?.amount || 0))}
                  </h5>
                  <Badge bg="secondary">{paymentDetails.payment?.request_status?.status}</Badge>
                </div>
              </div>

              <h6 className="mt-4 mb-2">{t("Audit History", "Audit History")}</h6>
              <div className="border border-secondary rounded p-2">
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
                  <div className="text-muted small text-center py-2">{t("No audit history for this payment.", "No audit history for this payment.")}</div>
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
