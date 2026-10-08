// React
import { MemoryRouter, Route, Routes } from "react-router-dom";

// Third Party
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NuqsTestingAdapter } from "nuqs/adapters/testing";
import { beforeEach, describe, expect, it, vi } from "vitest";

// AA TaxSystem
import * as ApiCalls from "@/Api/ApiCalls";
import type { components } from "@/Api/OpenApi";
import { PaymentsPage } from "@/Pages/Payments/PaymentsPage";

type PaymentRow = components["schemas"]["PaymentCorporationSchema"];

vi.mock("@/Api/ApiCalls", () => ({
  loadPayments: vi.fn(),
  loadPaymentDetails: vi.fn(),
  acceptPayment: vi.fn(),
  rejectPayment: vi.fn(),
  undoPayment: vi.fn(),
  deletePayment: vi.fn(),
  managePaymentAction: vi.fn(),
  manageBulkPaymentAction: vi.fn(),
}));

const mockPayments: PaymentRow[] = [
  {
    payment_id: 101,
    character: {
      character_id: 1001,
      character_name: "Pilot ESI Pending",
      character_portrait: "",
    },
    amount: 10000000,
    date: "2026-10-01",
    request_status: {
      status: "Pending",
      code: "pending",
      color: "warning",
    },
    division_name: "Master Wallet",
    reason: "Tax Auto Match",
    reviser: "—",
    is_custom: false,
    can_delete: false,
    can_approve: true,
    can_reject: true,
    can_undo: false,
  },
  {
    payment_id: 102,
    character: {
      character_id: 1002,
      character_name: "Pilot ESI Approved",
      character_portrait: "",
    },
    amount: 25000000,
    date: "2026-10-02",
    request_status: {
      status: "Approved",
      code: "approved",
      color: "success",
    },
    division_name: "Master Wallet",
    reason: "Tax Auto Match",
    reviser: "Auditor",
    is_custom: false,
    can_delete: false,
    can_approve: false,
    can_reject: false,
    can_undo: true,
  },
  {
    payment_id: 103,
    character: {
      character_id: 1003,
      character_name: "Pilot Custom Payment",
      character_portrait: "",
    },
    amount: 5000000,
    date: "2026-10-03",
    request_status: {
      status: "Pending",
      code: "pending",
      color: "warning",
    },
    division_name: "Cash Pool",
    reason: "Manual adjustment",
    reviser: "Director",
    is_custom: true,
    can_delete: true,
    can_approve: true,
    can_reject: true,
    can_undo: false,
  },
];

const renderPage = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/taxsystem/payments/10/"]}>
        <Routes>
          <Route
            path="/taxsystem/payments/:ownerId/"
            element={
              <NuqsTestingAdapter>
                <PaymentsPage />
              </NuqsTestingAdapter>
            }
          />
        </Routes>
      </MemoryRouter>
    </QueryClientProvider>,
  );
};

describe("PaymentsPage - Action Visibility and Permissions", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should show Accept and Reject for pending payment, but not Undo", async () => {
    // Test Data
    vi.mocked(ApiCalls.loadPayments).mockResolvedValue(mockPayments);

    // Test Action
    renderPage();

    // Expected Result
    await waitFor(() => {
      expect(screen.getByText("Pilot ESI Pending")).toBeInTheDocument();
    });

    const pendingRow = screen.getByText("Pilot ESI Pending").closest("tr")!;
    expect(pendingRow.querySelector("button[aria-label='Accept Payment']")).toBeInTheDocument();
    expect(pendingRow.querySelector("button[aria-label='Reject Payment']")).toBeInTheDocument();
    expect(pendingRow.querySelector("button[aria-label='Undo Payment']")).toBeNull();
  });

  it("should show Undo for approved payment, but not Accept or Reject", async () => {
    // Test Data
    vi.mocked(ApiCalls.loadPayments).mockResolvedValue(mockPayments);

    // Test Action
    renderPage();

    // Expected Result
    await waitFor(() => {
      expect(screen.getByText("Pilot ESI Approved")).toBeInTheDocument();
    });

    const approvedRow = screen.getByText("Pilot ESI Approved").closest("tr")!;
    expect(approvedRow.querySelector("button[aria-label='Undo Payment']")).toBeInTheDocument();
    expect(approvedRow.querySelector("button[aria-label='Accept Payment']")).toBeNull();
    expect(approvedRow.querySelector("button[aria-label='Reject Payment']")).toBeNull();
  });

  it("should NOT show Delete button for ESI payments", async () => {
    // Test Data
    vi.mocked(ApiCalls.loadPayments).mockResolvedValue(mockPayments);

    // Test Action
    renderPage();

    // Expected Result
    await waitFor(() => {
      expect(screen.getByText("Pilot ESI Pending")).toBeInTheDocument();
      expect(screen.getByText("Pilot ESI Approved")).toBeInTheDocument();
    });

    const pendingRow = screen.getByText("Pilot ESI Pending").closest("tr")!;
    const approvedRow = screen.getByText("Pilot ESI Approved").closest("tr")!;
    expect(pendingRow.querySelector("button[aria-label='Delete Custom Payment']")).toBeNull();
    expect(approvedRow.querySelector("button[aria-label='Delete Custom Payment']")).toBeNull();
  });

  it("should show Delete button for Custom payments and open confirmation modal", async () => {
    // Test Data
    const user = userEvent.setup();
    vi.mocked(ApiCalls.loadPayments).mockResolvedValue(mockPayments);

    // Test Action
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("Pilot Custom Payment")).toBeInTheDocument();
    });

    const customRow = screen.getByText("Pilot Custom Payment").closest("tr")!;
    const deleteBtn = customRow.querySelector("button[aria-label='Delete Custom Payment']")!;
    expect(deleteBtn).toBeInTheDocument();

    await user.click(deleteBtn);

    // Expected Result
    expect(screen.getByText("Delete Custom Payment")).toBeInTheDocument();
    expect(
      screen.getByText(/Are you sure you want to permanently delete this custom payment/i),
    ).toBeInTheDocument();
  });

  it("should show bulk actions toolbar when rows are selected and execute bulk approve", async () => {
    // Test Data
    const user = userEvent.setup();
    vi.mocked(ApiCalls.loadPayments).mockResolvedValue(mockPayments);
    vi.mocked(ApiCalls.manageBulkPaymentAction).mockResolvedValue({
      success: true,
      message: "2 payments processed successfully",
      processed_count: 2,
      total_count: 2,
    });

    // Test Action
    renderPage();
    await waitFor(() => {
      expect(screen.getByText("Pilot ESI Pending")).toBeInTheDocument();
    });

    // Check row 101 checkbox
    const checkbox101 = screen.getByLabelText("Select row", { selector: "#select-payment-101" });
    await user.click(checkbox101);

    // Expected Result - toolbar visible with 1 selected
    expect(screen.getByText("1 selected:")).toBeInTheDocument();

    // Check row 103 checkbox
    const checkbox103 = screen.getByLabelText("Select row", { selector: "#select-payment-103" });
    await user.click(checkbox103);

    // Expected Result - toolbar visible with 2 selected
    expect(screen.getByText("2 selected:")).toBeInTheDocument();

    // Test Action - click bulk Approve
    const approveBtn = screen.getByRole("button", { name: /^Approve$/i });
    await user.click(approveBtn);

    // Expected Result - bulk approve API called with [101, 103]
    expect(ApiCalls.manageBulkPaymentAction).toHaveBeenCalledWith(
      10,
      [101, 103],
      "approve",
      undefined,
    );
  });
});
