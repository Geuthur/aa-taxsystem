// React
import { useMemo } from "react";

// Third Party
import { useQuery, useQueryClient } from "@tanstack/react-query";
import { Image } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// AA TaxSystem
import { loadMemberPayments } from "@/Api/ApiCalls";
import type { components } from "@/Api/OpenApi";
import { queryKeys } from "@/Api/query";
import { BaseModal, ModalSize } from "@/Components/Base/BaseModal";
import { BaseTable } from "@/Components/Base/BaseTable";
import {
  PaymentActionButtons,
  PaymentActionModals,
} from "@/Components/Payments";
import { getPaymentColumns } from "@/Components/Tables";
import { usePaymentActions } from "@/Hooks/usePaymentActions";

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
    ownerId,
    onSuccess: invalidateAll,
  });

  const columns = useMemo(
    () =>
      getPaymentColumns<PaymentRow>({
        t,
        showCharacter: false,
        showReviser: true,
        renderActions: (p) => (
          <PaymentActionButtons
            payment={p}
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
    </>
  );
}

export default MemberPaymentsModal;
