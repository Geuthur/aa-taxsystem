// React
import { MemoryRouter, Route, Routes } from "react-router-dom";

// Third Party
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { NuqsTestingAdapter } from "nuqs/adapters/testing";
import { beforeEach, describe, expect, it, vi } from "vitest";

// AA TaxSystem
import * as ApiCalls from "@/Api/ApiCalls";
import OwnerManagePage from "@/Pages/OwnerManagePage";

vi.mock("@/Api/ApiCalls", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/Api/ApiCalls")>();
  return {
    ...actual,
    loadDashboard: vi.fn(),
    triggerOwnerUpdate: vi.fn(),
    deleteOwner: vi.fn(),
  };
});

const mockDashboardSuccess = {
  owner: {
    owner_id: 1001,
    owner_name: "Acme Corp",
    owner_type: "corporation",
  },
  update_status: {
    status: {
      wallet_journal: { is_success: true, last_update_finished_at: "2026-10-19T20:00:00Z" },
    },
    has_errors: false,
    status_display: "ok",
  },
  tax_amount: 10000000,
  tax_period: 30,
  divisions: {
    divisions: [{ id: 1, name: "Master", balance: 50000000 }],
    total_balance: 50000000,
  },
  statistics: {
    owner_id: 1001,
    owner_name: "Acme Corp",
  },
  activity: 25000000,
};

const mockDashboardError = {
  ...mockDashboardSuccess,
  update_status: {
    status: {
      wallet_journal: { is_success: false, last_update_finished_at: "2026-10-19T20:00:00Z" },
    },
    has_errors: true,
    status_display: "error",
  },
};

const renderComponent = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <NuqsTestingAdapter>
        <MemoryRouter initialEntries={["/owner/1001/"]}>
          <Routes>
            <Route path="/owner/:ownerId/" element={<OwnerManagePage />} />
          </Routes>
        </MemoryRouter>
      </NuqsTestingAdapter>
    </QueryClientProvider>,
  );
};

describe("OwnerManagePage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders SYNCHRONIZED when update status is successful", async () => {
    // Test Data
    vi.mocked(ApiCalls.loadDashboard).mockResolvedValue(mockDashboardSuccess as never);

    // Test Action
    renderComponent();

    // Expected Result
    expect(await screen.findByText("Acme Corp")).toBeInTheDocument();
    expect(screen.getByText("Synchronized")).toBeInTheDocument();
    expect(screen.queryByText("Sync Error")).not.toBeInTheDocument();
  });

  it("renders SYNC ERROR badge when update status has errors", async () => {
    // Test Data
    vi.mocked(ApiCalls.loadDashboard).mockResolvedValue(mockDashboardError as never);

    // Test Action
    renderComponent();

    // Expected Result
    expect(await screen.findByText("Acme Corp")).toBeInTheDocument();
    expect(screen.getByText("Sync Error")).toBeInTheDocument();
    expect(screen.queryByText("Synchronized")).not.toBeInTheDocument();
    // Per-section details are only shown on the Settings page
    expect(screen.queryByText("Failed")).not.toBeInTheDocument();
    expect(screen.queryByText("wallet_journal")).not.toBeInTheDocument();
  });

  it("does not render Update or Delete buttons in header (moved to Settings)", async () => {
    // Test Data
    vi.mocked(ApiCalls.loadDashboard).mockResolvedValue(mockDashboardSuccess as never);

    // Test Action
    renderComponent();

    // Expected Result
    expect(await screen.findByText("Acme Corp")).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /^Update/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("button", { name: /^Delete$/i })).not.toBeInTheDocument();
  });
});
