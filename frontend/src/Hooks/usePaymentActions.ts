// React
import { useState } from "react";

// Third Party
import { useMutation } from "@tanstack/react-query";

// AA TaxSystem
import { managePaymentAction } from "@/Api/ApiCalls";
import type { components } from "@/Api/OpenApi";

export type BasePaymentRow =
  | components["schemas"]["PaymentSchema"]
  | components["schemas"]["PaymentCorporationSchema"];

export interface UsePaymentActionsProps {
  ownerId: number;
  onSuccess?: () => void;
}

export function usePaymentActions({ ownerId, onSuccess }: UsePaymentActionsProps) {
  const [rejectingPayment, setRejectingPayment] = useState<BasePaymentRow | null>(null);
  const [rejectComment, setRejectComment] = useState("");

  const [deletingPayment, setDeletingPayment] = useState<BasePaymentRow | null>(null);
  const [deleteComment, setDeleteComment] = useState("");

  const actionMutation = useMutation({
    mutationFn: ({
      paymentPk,
      action,
      comment,
    }: {
      paymentPk: number;
      action: "approve" | "reject" | "undo" | "delete";
      comment?: string;
    }) => managePaymentAction(ownerId, paymentPk, action, comment),
    onSuccess: (_, variables) => {
      onSuccess?.();
      if (variables.action === "reject") {
        setRejectingPayment(null);
        setRejectComment("");
      }
      if (variables.action === "delete") {
        setDeletingPayment(null);
        setDeleteComment("");
      }
    },
  });

  const approve = (paymentPk: number) => {
    actionMutation.mutate({ paymentPk, action: "approve" });
  };

  const undo = (paymentPk: number) => {
    actionMutation.mutate({ paymentPk, action: "undo" });
  };

  const confirmReject = () => {
    if (rejectingPayment) {
      actionMutation.mutate({
        paymentPk: rejectingPayment.payment_id,
        action: "reject",
        comment: rejectComment.trim(),
      });
    }
  };

  const confirmDelete = () => {
    if (deletingPayment) {
      actionMutation.mutate({
        paymentPk: deletingPayment.payment_id,
        action: "delete",
        comment: deleteComment.trim() || undefined,
      });
    }
  };

  return {
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
    isPending: actionMutation.isPending,
  };
}

export default usePaymentActions;
