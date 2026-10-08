// React
import React from "react";

// Third Party
import { Check, Eye, Trash2, Undo2, X } from "lucide-react";
import { Button, Spinner } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// AA TaxSystem
import type { BasePaymentRow } from "@/Hooks/usePaymentActions";
import { renderTooltip } from "@/Utils";

export interface PaymentActionButtonsProps {
  payment: BasePaymentRow;
  onViewDetails?: (paymentId: number) => void;
  onApprove?: (paymentId: number) => void;
  onReject?: (payment: BasePaymentRow) => void;
  onUndo?: (paymentId: number) => void;
  onDelete?: (payment: BasePaymentRow) => void;
  isPending?: boolean;
}

export const PaymentActionButtons: React.FC<PaymentActionButtonsProps> = ({
  payment,
  onViewDetails,
  onApprove,
  onReject,
  onUndo,
  onDelete,
  isPending = false,
}) => {
  const { t } = useTranslation();

  const statusCode = (
    payment.request_status?.code ||
    payment.request_status?.status ||
    ""
  ).toLowerCase();

  const isPendingStatus =
    payment.can_approve ??
    (statusCode === "pending" || statusCode === "needs_approval");

  const isProcessedStatus =
    payment.can_undo ??
    (statusCode === "approved" || statusCode === "rejected");

  const canDelete = Boolean(payment.can_delete ?? payment.is_custom);

  return (
    <div className="d-flex align-items-center gap-1">
      {onViewDetails &&
        renderTooltip(
          t("View Details"),
          <Button
            className="aa-btn aa-btn-sm aa-btn-info"
            aria-label={t("View Details")}
            onClick={() => onViewDetails(payment.payment_id)}
          >
            <Eye size={12} />
          </Button>,
        )}

      {isPendingStatus && onApprove && (
        renderTooltip(
          t("Accept Payment"),
          <Button
            className="aa-btn aa-btn-sm aa-btn-success"
            aria-label={t("Accept Payment")}
            disabled={isPending}
            onClick={() => onApprove(payment.payment_id)}
          >
            {isPending ? <Spinner size="sm" animation="border" /> : <Check size={12} />}
          </Button>,
        )
      )}

      {isPendingStatus && onReject && (
        renderTooltip(
          t("Reject Payment"),
          <Button
            className="aa-btn aa-btn-sm aa-btn-danger"
            aria-label={t("Reject Payment")}
            disabled={isPending}
            onClick={() => onReject(payment)}
          >
            <X size={12} />
          </Button>,
        )
      )}

      {isProcessedStatus && onUndo && (
        renderTooltip(
          t("Undo Payment"),
          <Button
            className="aa-btn aa-btn-sm aa-btn-warning"
            aria-label={t("Undo Payment")}
            disabled={isPending}
            onClick={() => onUndo(payment.payment_id)}
          >
            {isPending ? <Spinner size="sm" animation="border" /> : <Undo2 size={12} />}
          </Button>,
        )
      )}

      {canDelete && onDelete && (
        renderTooltip(
          t("Delete Custom Payment"),
          <Button
            className="aa-btn aa-btn-sm aa-btn-danger"
            aria-label={t("Delete Custom Payment")}
            disabled={isPending}
            onClick={() => onDelete(payment)}
          >
            <Trash2 size={12} />
          </Button>,
        )
      )}
    </div>
  );
};

export default PaymentActionButtons;
