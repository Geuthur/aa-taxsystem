// React
import { MemoryRouter } from "react-router-dom";

// Third Party
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NuqsTestingAdapter } from "nuqs/adapters/testing";
import { beforeEach, describe, expect, it, vi } from "vitest";

// AA TaxSystem
import * as ApiCalls from "@/Api/ApiCalls";
import type { SuperuserTaxOwnerSchema } from "@/Api/schema";
import { SuperuserPage } from "@/Pages/SuperuserPage";

vi.mock("@/Api/ApiCalls", () => ({
  loadSuperuserOwners: vi.fn(),
  runAdminTasks: vi.fn(),
  triggerSuperuserOwnerUpdate: vi.fn(),
  deleteSuperuserOwner: vi.fn(),
  loadDashboard: vi.fn(),
  updateOwnerSettings: vi.fn(),
}));

const mockOwners: SuperuserTaxOwnerSchema[] = [
  {
    id: 1,
    owner_id: 101,
    owner_type: "corporation",
    name: "Alpha Mining Corp",
    icon: "https://images.evetech.net/corporations/101/logo",
    ticker: "AMC",
    status: "ok",
    is_active: true,
    tax_amount: 15000000,
    tax_period: 30,
    open_invoices: 0,
    last_sync: "2026-10-18T12:00:00Z",
    error_message: null,
  },
  {
    id: 2,
    owner_id: 201,
    owner_type: "alliance",
    name: "Northern Coalition",
    icon: "https://images.evetech.net/alliances/201/logo",
    ticker: "NC",
    status: "error",
    is_active: true,
    tax_amount: 25000000,
    tax_period: 14,
    open_invoices: 3,
    last_sync: "2026-10-17T08:00:00Z",
    error_message: "ESI Token Expired",
  },
];

const mockDashboard = {
  owner: {
    owner_id: 101,
    owner_name: "Alpha Mining Corp",
    owner_type: "corporation",
  },
  update_status: {
    status: {},
  },
  tax_amount: 15000000,
  tax_period: 30,
  divisions: {
    divisions: [],
  },
  statistics: {
    tax_account: {
      accounts: 10,
      accounts_active: 8,
      accounts_inactive: 2,
      accounts_deactivated: 0,
      accounts_paid: 5,
      accounts_unpaid: 3,
    },
    payments: {
      payments: 25,
      payments_pending: 2,
      payments_approved: 20,
      payments_automatic: 15,
      payments_manual: 5,
    },
    members: {
      members: 12,
      members_unregistered: 2,
      members_alts: 5,
      members_mains: 7,
    },
  },
  activity: 0,
};

const renderPage = (searchParams?: string) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <NuqsTestingAdapter searchParams={searchParams} hasMemory>
          <SuperuserPage />
        </NuqsTestingAdapter>
      </MemoryRouter>
    </QueryClientProvider>,
  );
};

describe("SuperuserPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.mocked(ApiCalls.loadSuperuserOwners).mockResolvedValue(mockOwners);
    vi.mocked(ApiCalls.loadDashboard).mockResolvedValue(mockDashboard as never);
  });

  it("should render superuser overview with metrics, task panel, and owners table", async () => {
    // Test Data
    renderPage();

    // Test Action
    await waitFor(() => {
      expect(screen.getByText("Superuser Administration")).toBeInTheDocument();
    });

    // Expected Result
    await waitFor(() => {
      expect(screen.getByText("Total Owners")).toBeInTheDocument();
      expect(screen.getByText("Alpha Mining Corp")).toBeInTheDocument();
      expect(screen.getByText("Northern Coalition")).toBeInTheDocument();
    });
  });

  it("should toggle global task panel and trigger update all tasks with force refresh switch", async () => {
    // Test Data
    const user = userEvent.setup();
    vi.mocked(ApiCalls.runAdminTasks).mockResolvedValue({
      message: "Queued Update All Taxsystem",
    });
    renderPage();

    await waitFor(() => {
      expect(screen.getByText("Global Task Administration")).toBeInTheDocument();
    });

    // Test Action
    const toggle = screen.getByTestId("toggle-task-panel");
    fireEvent.click(toggle);

    const forceSwitch = await screen.findByLabelText(/Force Refresh ESI/i);
    await user.click(forceSwitch);

    const updateAllButton = await screen.findByRole("button", { name: /^Update All$/i });
    await user.click(updateAllButton);

    // Expected Result
    await waitFor(() => {
      expect(ApiCalls.runAdminTasks).toHaveBeenCalledWith({
        target: "all",
        force_refresh: true,
      });
      expect(screen.getByTestId("task-feedback-message")).toHaveTextContent(
        "Queued Update All Taxsystem",
      );
    });
  });

  it("should filter owners by type buttons, issues, and search", async () => {
    // Test Data
    const user = userEvent.setup();
    renderPage();

    await waitFor(() => {
      expect(screen.getByText("Alpha Mining Corp")).toBeInTheDocument();
    });

    // Test Action 1: Filter by Alliance
    const allianceFilterButton = screen.getByRole("button", { name: /^Alliances/i });
    await user.click(allianceFilterButton);

    // Expected Result 1
    expect(screen.queryByText("Alpha Mining Corp")).not.toBeInTheDocument();
    expect(screen.getByText("Northern Coalition")).toBeInTheDocument();

    // Test Action 2: Filter by Issues
    const issuesFilterButton = screen.getByRole("button", { name: /^Issues/i });
    await user.click(issuesFilterButton);

    // Expected Result 2
    expect(screen.queryByText("Alpha Mining Corp")).not.toBeInTheDocument();
    expect(screen.getByText("Northern Coalition")).toBeInTheDocument();

    // Test Action 3: Reset to All and Search
    const allFilterButton = screen.getByRole("button", { name: /^All /i });
    await user.click(allFilterButton);

    const searchInput = screen.getByPlaceholderText(/Search by name or ticker/i);
    await user.type(searchInput, "AMC");

    // Expected Result 3
    expect(screen.getByText("Alpha Mining Corp")).toBeInTheDocument();
    expect(screen.queryByText("Northern Coalition")).not.toBeInTheDocument();
  });

  it("should trigger update for a specific owner", async () => {
    // Test Data
    const user = userEvent.setup();
    vi.mocked(ApiCalls.triggerSuperuserOwnerUpdate).mockResolvedValue({
      message: "Queued update for Alpha Mining Corp",
    });
    renderPage();

    await waitFor(() => {
      expect(screen.getByText("Alpha Mining Corp")).toBeInTheDocument();
    });

    // Test Action
    const updateButtons = screen.getAllByTitle("Update");
    await user.click(updateButtons[0]);

    // Expected Result
    await waitFor(() => {
      expect(ApiCalls.triggerSuperuserOwnerUpdate).toHaveBeenCalledWith({
        ownerType: "corporation",
        ownerId: 101,
        payload: { force_refresh: false },
      });
      expect(screen.getByTestId("task-feedback-message")).toHaveTextContent(
        "Queued update for Alpha Mining Corp",
      );
    });
  });

  it("should open delete modal and confirm deletion of owner", async () => {
    // Test Data
    const user = userEvent.setup();
    vi.mocked(ApiCalls.deleteSuperuserOwner).mockResolvedValue({
      message: "Corporation Alpha Mining Corp deleted successfully.",
    });
    renderPage();

    await waitFor(() => {
      expect(screen.getByText("Alpha Mining Corp")).toBeInTheDocument();
    });

    // Test Action
    const deleteButtons = screen.getAllByTitle("Delete");
    await user.click(deleteButtons[0]);

    // Verify modal appeared
    expect(await screen.findByText("Confirm Owner Deletion")).toBeInTheDocument();

    const confirmButton = screen.getByRole("button", { name: "Delete Owner" });
    await user.click(confirmButton);

    // Expected Result
    await waitFor(() => {
      expect(ApiCalls.deleteSuperuserOwner).toHaveBeenCalledWith({
        ownerType: "corporation",
        ownerId: 101,
      });
      expect(screen.getByTestId("task-feedback-message")).toHaveTextContent(
        "Corporation Alpha Mining Corp deleted successfully.",
      );
    });
  });

  it("should switch to inspection view when inspect query param is present and go back", async () => {
    // Test Data
    const user = userEvent.setup();
    renderPage("?inspect=101&type=corporation");

    // Test Action 1: Render inspection view
    expect(
      await screen.findByRole("button", { name: "Back to Superuser Overview" }),
    ).toBeInTheDocument();

    // Expected Result 1: Inspection view is rendered
    expect(screen.getByText("Tax Settings")).toBeInTheDocument();

    // Test Action 2: Click Back button
    const backButton = screen.getByRole("button", { name: "Back to Superuser Overview" });
    await user.click(backButton);

    // Expected Result 2: Restored to Superuser Overview
    await waitFor(() => {
      expect(screen.getByText("Superuser Administration")).toBeInTheDocument();
    });
  });

  it("should open inspection view when clicking inspect button from table", async () => {
    // Test Data
    const user = userEvent.setup();
    renderPage();

    await waitFor(() => {
      expect(screen.getByText("Alpha Mining Corp")).toBeInTheDocument();
    });

    // Test Action
    const inspectButtons = screen.getAllByRole("button", { name: "Inspect" });
    await user.click(inspectButtons[0]);

    // Expected Result
    expect(
      await screen.findByRole("button", { name: "Back to Superuser Overview" }),
    ).toBeInTheDocument();
  });
});
