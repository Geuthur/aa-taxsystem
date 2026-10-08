// React
import React from "react";

// Third Party
import { Trash2 } from "lucide-react";
import { Button, Form, Spinner } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// AA TaxSystem
import { BaseModal, ModalSize } from "@/Components/Base/BaseModal";
import type { BasePaymentRow } from "@/Hooks/usePaymentActions";
import { formatNumber } from "@/Utils";

export interface PaymentActionModalsProps {
  rejectingPayment: BasePaymentRow | null;
  rejectComment: string;
  onRejectCommentChange: (comment: string) => void;
  onCancelReject: () => void;
  onConfirmReject: () => void;

  deletingPayment: BasePaymentRow | null;
  deleteComment: string;
  onDeleteCommentChange: (comment: string) => void;
  onCancelDelete: () => void;
  onConfirmDelete: () => void;

  isPending?: boolean;
}

export const PaymentActionModals: React.FC<PaymentActionModalsProps> = ({
  rejectingPayment,
  rejectComment,
  onRejectCommentChange,
  onCancelReject,
  onConfirmReject,
  deletingPayment,
  deleteComment,
  onDeleteCommentChange,
  onCancelDelete,
  onConfirmDelete,
  isPending = false,
}) => {
  const { t } = useTranslation();

  return (
    <>
      {/* Reject Payment Modal */}
      {rejectingPayment && (
        <BaseModal
          show={!!rejectingPayment}
          onHide={onCancelReject}
          size={ModalSize.medium}
          title={
            <div className="h5 d-flex align-items-center gap-2 text-danger mb-0">
              {t("Reject Payment")}
            </div>
          }
          footer={
            <>
              <Button variant="secondary" onClick={onCancelReject}>
                {t("Cancel")}
              </Button>
              <Button
                variant="danger"
                disabled={isPending}
                onClick={onConfirmReject}
              >
                {isPending && (
                  <Spinner size="sm" animation="border" className="me-1" />
                )}
                {t("Confirm Rejection")}
              </Button>
            </>
          }
        >
          <p>
            {t("Rejecting payment of")}{" "}
            <strong>{formatNumber(Number(rejectingPayment.amount || 0))}</strong>
            {"character" in rejectingPayment && rejectingPayment.character?.character_name ? (
              <>
                {" "}
                {t("from")}{" "}
                <strong>{rejectingPayment.character.character_name}</strong>.
              </>
            ) : (
              "."
            )}
          </p>
          <Form.Group className="mb-3">
            <Form.Label>{t("Rejection Reason / Comment")}</Form.Label>
            <Form.Control
              as="textarea"
              rows={3}
              value={rejectComment}
              onChange={(e) => onRejectCommentChange(e.target.value)}
              placeholder={t("Reason for rejecting payment...")}
              className="bg-dark text-light border-secondary"
            />
          </Form.Group>
        </BaseModal>
      )}

      {/* Delete Custom Payment Modal */}
      {deletingPayment && (
        <BaseModal
          show={!!deletingPayment}
          onHide={onCancelDelete}
          size={ModalSize.medium}
          title={
            <div className="h5 d-flex align-items-center gap-2 text-danger mb-0">
              <Trash2 size={18} />
              {t("Delete Custom Payment")}
            </div>
          }
          footer={
            <>
              <Button variant="secondary" onClick={onCancelDelete}>
                {t("Cancel")}
              </Button>
              <Button
                variant="danger"
                disabled={isPending}
                onClick={onConfirmDelete}
              >
                {isPending && (
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
            </strong>
            {"character" in deletingPayment && deletingPayment.character?.character_name ? (
              <>
                {" "}
                {t("from")}{" "}
                <strong>{deletingPayment.character.character_name}</strong>?
              </>
            ) : (
              "?"
            )}
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
              onChange={(e) => onDeleteCommentChange(e.target.value)}
              placeholder={t("Reason for deleting this custom payment...")}
              className="bg-dark text-light border-secondary"
            />
          </Form.Group>
        </BaseModal>
      )}
    </>
  );
};

export default PaymentActionModals;
