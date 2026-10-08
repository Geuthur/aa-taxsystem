// Third Party
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

// AA TaxSystem
import { PaymentActionModals } from "@/Components/Payments/PaymentActionModals";
import type { BasePaymentRow } from "@/Hooks/usePaymentActions";

const baseMockPayment: BasePaymentRow = {
  payment_id: 10,
  amount: 15000000,
  date: "2026-10-01",
  request_status: { code: "pending", status: "Pending", color: "warning" },
  division_name: "Wallet 1",
  reason: "Corp tax",
  reviser: "—",
  is_custom: false,
  can_delete: false,
  can_approve: true,
  can_reject: true,
  can_undo: false,
};

describe("PaymentActionModals Component", () => {
  it("renders reject modal and handles input and confirm rejection", async () => {
    // Test Data
    const handleCommentChange = vi.fn();
    const handleCancel = vi.fn();
    const handleConfirm = vi.fn();
    const payment = { ...baseMockPayment };

    // Test Action
    render(
      <PaymentActionModals
        rejectingPayment={payment}
        rejectComment="Not enough ISK"
        onRejectCommentChange={handleCommentChange}
        onCancelReject={handleCancel}
        onConfirmReject={handleConfirm}
        deletingPayment={null}
        deleteComment=""
        onDeleteCommentChange={() => {}}
        onCancelDelete={() => {}}
        onConfirmDelete={() => {}}
      />,
    );

    const textarea = screen.getByPlaceholderText("Reason for rejecting payment...");
    await userEvent.type(textarea, " more info");

    const confirmBtn = screen.getByRole("button", { name: "Confirm Rejection" });
    await userEvent.click(confirmBtn);

    // Expected Result
    expect(screen.getByText("Reject Payment")).toBeInTheDocument();
    expect(handleCommentChange).toHaveBeenCalled();
    expect(handleConfirm).toHaveBeenCalled();
  });

  it("renders delete modal and handles cancel and confirm deletion", async () => {
    // Test Data
    const handleCancel = vi.fn();
    const handleConfirm = vi.fn();
    const payment = {
      ...baseMockPayment,
      payment_id: 20,
      amount: 25000000,
      is_custom: true,
      can_delete: true,
    };

    // Test Action
    render(
      <PaymentActionModals
        rejectingPayment={null}
        rejectComment=""
        onRejectCommentChange={() => {}}
        onCancelReject={() => {}}
        onConfirmReject={() => {}}
        deletingPayment={payment}
        deleteComment=""
        onDeleteCommentChange={() => {}}
        onCancelDelete={handleCancel}
        onConfirmDelete={handleConfirm}
      />,
    );

    const cancelBtn = screen.getByRole("button", { name: "Cancel" });
    await userEvent.click(cancelBtn);

    const confirmBtn = screen.getByRole("button", { name: "Confirm Deletion" });
    await userEvent.click(confirmBtn);

    // Expected Result
    expect(screen.getByText("Delete Custom Payment")).toBeInTheDocument();
    expect(handleCancel).toHaveBeenCalled();
    expect(handleConfirm).toHaveBeenCalled();
  });
});
