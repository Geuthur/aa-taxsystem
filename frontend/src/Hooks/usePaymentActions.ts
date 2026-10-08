// React
import { useState } from "react";

// Third Party
import { useMutation } from "@tanstack/react-query";

// AA TaxSystem
import { manageBulkPaymentAction, managePaymentAction } from "@/Api/ApiCalls";
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

  const [bulkRejectingPaymentIds, setBulkRejectingPaymentIds] = useState<number[] | null>(null);
  const [bulkRejectComment, setBulkRejectComment] = useState("");

  const [bulkDeletingPaymentIds, setBulkDeletingPaymentIds] = useState<number[] | null>(null);
  const [bulkDeleteComment, setBulkDeleteComment] = useState("");

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

  const bulkActionMutation = useMutation({
    mutationFn: ({
      paymentIds,
      action,
      comment,
    }: {
      paymentIds: number[];
      action: "approve" | "reject" | "undo" | "delete";
      comment?: string;
    }) => manageBulkPaymentAction(ownerId, paymentIds, action, comment),
    onSuccess: (_, variables) => {
      onSuccess?.();
      if (variables.action === "reject") {
        setBulkRejectingPaymentIds(null);
        setBulkRejectComment("");
      }
      if (variables.action === "delete") {
        setBulkDeletingPaymentIds(null);
        setBulkDeleteComment("");
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

  const bulkApprove = (paymentIds: number[]) => {
    if (paymentIds.length > 0) {
      bulkActionMutation.mutate({ paymentIds, action: "approve" });
    }
  };

  const bulkUndo = (paymentIds: number[]) => {
    if (paymentIds.length > 0) {
      bulkActionMutation.mutate({ paymentIds, action: "undo" });
    }
  };

  const confirmBulkReject = () => {
    if (bulkRejectingPaymentIds && bulkRejectingPaymentIds.length > 0) {
      bulkActionMutation.mutate({
        paymentIds: bulkRejectingPaymentIds,
        action: "reject",
        comment: bulkRejectComment.trim(),
      });
    }
  };

  const confirmBulkDelete = () => {
    if (bulkDeletingPaymentIds && bulkDeletingPaymentIds.length > 0) {
      bulkActionMutation.mutate({
        paymentIds: bulkDeletingPaymentIds,
        action: "delete",
        comment: bulkDeleteComment.trim() || undefined,
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
    // Bulk actions
    bulkApprove,
    bulkUndo,
    bulkRejectingPaymentIds,
    setBulkRejectingPaymentIds,
    bulkRejectComment,
    setBulkRejectComment,
    confirmBulkReject,
    bulkDeletingPaymentIds,
    setBulkDeletingPaymentIds,
    bulkDeleteComment,
    setBulkDeleteComment,
    confirmBulkDelete,
    isPending: actionMutation.isPending || bulkActionMutation.isPending,
  };
}

export default usePaymentActions;
