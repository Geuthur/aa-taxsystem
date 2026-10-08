// Third Party
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

// AA TaxSystem
import { PaymentActionButtons } from "@/Components/Payments/PaymentActionButtons";
import type { BasePaymentRow } from "@/Hooks/usePaymentActions";

const baseMockPayment: BasePaymentRow = {
  payment_id: 42,
  amount: 1000,
  date: "2026-10-01",
  request_status: { code: "pending", status: "Pending", color: "warning" },
  division_name: "Wallet 1",
  reason: "Tax test",
  reviser: "—",
  is_custom: false,
  can_delete: false,
  can_approve: true,
  can_reject: true,
  can_undo: false,
};

describe("PaymentActionButtons Component", () => {
  it("renders pending action buttons and triggers approve and reject", async () => {
    // Test Data
    const handleApprove = vi.fn();
    const handleReject = vi.fn();
    const payment = { ...baseMockPayment };

    // Test Action
    render(
      <PaymentActionButtons
        payment={payment}
        onApprove={handleApprove}
        onReject={handleReject}
      />,
    );

    const acceptBtn = screen.getByRole("button", { name: "Accept Payment" });
    const rejectBtn = screen.getByRole("button", { name: "Reject Payment" });

    await userEvent.click(acceptBtn);
    await userEvent.click(rejectBtn);

    // Expected Result
    expect(handleApprove).toHaveBeenCalledWith(42);
    expect(handleReject).toHaveBeenCalledWith(payment);
  });

  it("renders undo button for processed payments", async () => {
    // Test Data
    const handleUndo = vi.fn();
    const payment = {
      ...baseMockPayment,
      payment_id: 43,
      amount: 5000,
      date: "2026-10-02",
      request_status: { code: "approved", status: "Approved", color: "success" },
      can_approve: false,
      can_undo: true,
    };

    // Test Action
    render(
      <PaymentActionButtons
        payment={payment}
        onUndo={handleUndo}
      />,
    );

    const undoBtn = screen.getByRole("button", { name: "Undo Payment" });
    await userEvent.click(undoBtn);

    // Expected Result
    expect(handleUndo).toHaveBeenCalledWith(43);
  });

  it("renders delete button for custom payments", async () => {
    // Test Data
    const handleDelete = vi.fn();
    const payment = {
      ...baseMockPayment,
      payment_id: 44,
      amount: 2000,
      date: "2026-10-03",
      request_status: { code: "approved", status: "Approved", color: "success" },
      is_custom: true,
      can_delete: true,
    };

    // Test Action
    render(
      <PaymentActionButtons
        payment={payment}
        onDelete={handleDelete}
      />,
    );

    const deleteBtn = screen.getByRole("button", { name: "Delete Custom Payment" });
    await userEvent.click(deleteBtn);

    // Expected Result
    expect(handleDelete).toHaveBeenCalledWith(payment);
  });
});
