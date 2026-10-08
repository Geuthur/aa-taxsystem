// React
import { useMemo, useState } from "react";

// Third Party
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { type ColumnDef } from "@tanstack/react-table";
import { Check, RotateCcw, Trash2, X } from "lucide-react";
import {
  Badge,
  Button,
  Form,
  Image,
  Spinner,
} from "react-bootstrap";
import { useTranslation } from "react-i18next";

// AA TaxSystem
import {
  approvePayment,
  deletePayment,
  loadMemberPayments,
  rejectPayment,
  undoPayment,
} from "@/Api/ApiCalls";
import type { components } from "@/Api/OpenApi";
import { queryKeys } from "@/Api/query";
import { BaseModal, ModalSize } from "@/Components/Base/BaseModal";
import { BaseTable } from "@/Components/Base/BaseTable";
import { formatNumber, renderTooltip } from "@/Utils";

type PaymentRow = components["schemas"]["PaymentSchema"];

interface MemberPaymentsModalProps {
  ownerId: number;
  characterId: number | null;
  characterName: string;
  characterPortrait?: string;
  show: boolean;
  onClose: () => void;
}

export function MemberPaymentsModal({
  ownerId,
  characterId,
  characterName,
  characterPortrait,
  show,
  onClose,
}: MemberPaymentsModalProps) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();

  const [rejectingPaymentId, setRejectingPaymentId] = useState<number | null>(null);
  const [rejectComment, setRejectComment] = useState("");

  const [deletingPayment, setDeletingPayment] = useState<PaymentRow | null>(null);
  const [deleteComment, setDeleteComment] = useState("");

  const {
    data: payments,
    isLoading,
    isError,
  } = useQuery({
    queryKey: characterId ? queryKeys.MemberPayments(ownerId, characterId) : ["MemberPayments", ownerId],
    queryFn: () => (characterId ? loadMemberPayments(ownerId, characterId) : Promise.resolve([])),
    enabled: show && characterId !== null,
  });

  const invalidateAll = () => {
    if (characterId) {
      queryClient.invalidateQueries({
        queryKey: queryKeys.MemberPayments(ownerId, characterId),
      });
    }
    queryClient.invalidateQueries({ queryKey: queryKeys.TaxAccounts(ownerId) });
    queryClient.invalidateQueries({ queryKey: queryKeys.Payments(ownerId) });
    queryClient.invalidateQueries({ queryKey: queryKeys.Dashboard(ownerId) });
  };

  const approveMutation = useMutation({
    mutationFn: (paymentId: number) => approvePayment(ownerId, paymentId),
    onSuccess: () => {
      invalidateAll();
    },
  });

  const rejectMutation = useMutation({
    mutationFn: ({ paymentId, comment }: { paymentId: number; comment?: string }) =>
      rejectPayment(ownerId, paymentId, comment),
    onSuccess: () => {
      invalidateAll();
      setRejectingPaymentId(null);
      setRejectComment("");
    },
  });

  const undoMutation = useMutation({
    mutationFn: (paymentId: number) => undoPayment(ownerId, paymentId),
    onSuccess: () => {
      invalidateAll();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: ({ paymentPk, comment }: { paymentPk: number; comment?: string }) =>
      deletePayment(ownerId, paymentPk, comment),
    onSuccess: () => {
      invalidateAll();
      setDeletingPayment(null);
      setDeleteComment("");
    },
  });

  const columns = useMemo<ColumnDef<PaymentRow>[]>(
    () => [
      {
        id: "date",
        header: t("Date"),
        accessorKey: "date",
        cell: ({ getValue }) => <span className="small">{String(getValue())}</span>,
      },
      {
        id: "division_name",
        header: t("Division"),
        accessorKey: "division_name",
        cell: ({ getValue }) => <span>{String(getValue() || "—")}</span>,
      },
      {
        id: "reason",
        header: t("Reason"),
        accessorKey: "reason",
        cell: ({ getValue }) => <span>{String(getValue() || "—")}</span>,
      },
      {
        id: "amount",
        header: t("Amount"),
        accessorKey: "amount",
        cell: ({ getValue }) => {
          const val = Number(getValue() || 0);
          return <span className="fw-semibold text-info">{formatNumber(val)}</span>;
        },
      },
      {
        id: "request_status",
        header: t("Status"),
        accessorFn: (row) => row.request_status?.status,
        cell: ({ row }) => {
          const status = row.original.request_status;
          return <Badge bg={status?.color || "secondary"}>{status?.status || t("Unknown")}</Badge>;
        },
      },
      {
        id: "reviser",
        header: t("Reviser"),
        accessorKey: "reviser",
        cell: ({ getValue }) => (
          <span className="small text-muted">{String(getValue() || "—")}</span>
        ),
      },
      {
        id: "actions",
        header: t("Actions"),
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
              {isPending && (
                <>
                  {renderTooltip(
                    t("Approve Payment"),
                    <Button
                      className="aa-btn aa-btn-sm aa-btn-success"
                      disabled={approveMutation.isPending}
                      onClick={() => approveMutation.mutate(p.payment_id)}
                    >
                      <Check size={14} />
                    </Button>,
                  )}
                  {renderTooltip(
                    t("Reject Payment"),
                    <Button
                      className="aa-btn aa-btn-sm aa-btn-danger"
                      disabled={rejectMutation.isPending}
                      onClick={() => {
                        setRejectingPaymentId(p.payment_id);
                        setRejectComment("");
                      }}
                    >
                      <X size={14} />
                    </Button>,
                  )}
                </>
              )}
              {isProcessed &&
                renderTooltip(
                  t("Undo Payment"),
                  <Button
                    className="aa-btn aa-btn-sm aa-btn-warning"
                    disabled={undoMutation.isPending}
                    onClick={() => undoMutation.mutate(p.payment_id)}
                  >
                    <RotateCcw size={14} />
                  </Button>,
                )}
              {canDelete &&
                renderTooltip(
                  t("Delete Custom Payment"),
                  <Button
                    className="aa-btn aa-btn-sm aa-btn-danger"
                    disabled={deleteMutation.isPending}
                    onClick={() => {
                      setDeletingPayment(p);
                      setDeleteComment("");
                    }}
                  >
                    <Trash2 size={14} />
                  </Button>,
                )}
            </div>
          );
        },
      },
    ],
    [t, approveMutation, rejectMutation, undoMutation, deleteMutation],
  );

  return (
    <>
      <BaseModal
        show={show}
        onHide={onClose}
        size={ModalSize.extraLarge}
        title={
          <div className="d-flex align-items-center gap-3">
            {characterPortrait && (
              <Image
                src={characterPortrait}
                roundedCircle
                width={40}
                height={40}
                alt={characterName}
              />
            )}
            <div>
              <div className="h5 mb-0">{characterName}</div>
              <small className="fs-6">
                {t("Payment History & Activities")}
              </small>
            </div>
          </div>
        }
        bodyClassName="aa-panel"
      >
        {isError ? (
          <div className="p-4 text-center text-danger">
            {t("Failed to load member payments.")}
          </div>
        ) : (
          <BaseTable
            variant="vowra-light"
            data={payments || []}
            columns={columns}
            isFetching={isLoading}
            emptyText={t("No payments found for this member.")}
          />
        )}
      </BaseModal>

      {/* Reject Modal with optional comment */}
      {rejectingPaymentId !== null && (
        <BaseModal
          show={rejectingPaymentId !== null}
          onHide={() => setRejectingPaymentId(null)}
          size={ModalSize.medium}
          title={<span className="h5 text-danger mb-0">{t("Reject Payment")}</span>}
          footer={
            <>
              <Button
                variant="secondary"
                onClick={() => setRejectingPaymentId(null)}
              >
                {t("Cancel")}
              </Button>
              <Button
                variant="danger"
                disabled={rejectMutation.isPending}
                onClick={() =>
                  rejectMutation.mutate({
                    paymentId: rejectingPaymentId,
                    comment: rejectComment,
                  })
                }
              >
                {rejectMutation.isPending && (
                  <Spinner size="sm" animation="border" className="me-1" />
                )}
                {t("Confirm Reject")}
              </Button>
            </>
          }
        >
          <Form.Group>
            <Form.Label>{t("Reason / Comment")}</Form.Label>
            <Form.Control
              as="textarea"
              rows={3}
              placeholder={t("Optional rejection reason")}
              value={rejectComment}
              onChange={(e) => setRejectComment(e.target.value)}
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
              {t("Delete Custom Payment")}
            </div>
          }
          footer={
            <>
              <Button
                variant="secondary"
                onClick={() => setDeletingPayment(null)}
              >
                {t("Cancel")}
              </Button>
              <Button
                variant="danger"
                disabled={deleteMutation.isPending}
                onClick={() =>
                  deleteMutation.mutate({
                    paymentPk: deletingPayment.payment_id,
                    comment: deleteComment || t("Deleted via Tax System"),
                  })
                }
              >
                {deleteMutation.isPending && (
                  <Spinner size="sm" animation="border" className="me-1" />
                )}
                {t("Confirm Deletion")}
              </Button>
            </>
          }
        >
          <p>
            {t("Are you sure you want to permanently delete this custom payment of")}{" "}
            <strong className="text-danger">
              {formatNumber(Number(deletingPayment.amount || 0))}
            </strong>?
          </p>
          {deletingPayment.request_status?.code === "approved" && (
            <div className="alert alert-warning small mb-3">
              {t(
                "This payment was already approved. Deleting it will automatically deduct this amount from the member's account deposit.",
              )}
            </div>
          )}
          <Form.Group className="mb-3">
            <Form.Label>{t("Deletion Reason / Comment")}</Form.Label>
            <Form.Control
              as="textarea"
              rows={3}
              value={deleteComment}
              onChange={(e) => setDeleteComment(e.target.value)}
              placeholder={t("Reason for deleting this custom payment...")}
              className="bg-dark text-light border-secondary"
            />
          </Form.Group>
        </BaseModal>
      )}
    </>
  );
}

export default MemberPaymentsModal;
