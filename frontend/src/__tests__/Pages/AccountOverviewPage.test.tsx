// React
import { MemoryRouter } from "react-router-dom";

// Third Party
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NuqsTestingAdapter } from "nuqs/adapters/testing";
import { beforeEach, describe, expect, it, vi } from "vitest";

// AA TaxSystem
import * as ApiCalls from "@/Api/ApiCalls";
import type { components } from "@/Api/OpenApi";
import { AccountOverviewPage } from "@/Pages/Account/AccountOverviewPage";

type UserAccount = components["schemas"]["UserAccountSchema"];

vi.mock("@/Api/ApiCalls", () => ({
  loadUserAccounts: vi.fn(),
}));

const mockAccounts: UserAccount[] = [
  {
    id: 1,
    name: "John Doe",
    owner_id: 101,
    owner_name: "Mega Corp",
    owner_type: "corporation",
    owner_logo: "https://images.evetech.net/corporations/101/logo",
    character_id: 2001,
    character_name: "John Doe",
    character_portrait: "https://images.evetech.net/characters/2001/portrait",
    status: "active",
    status_display: "Active",
    deposit: 15000000,
    tax_amount: 10000000,
    tax_period: 30,
    has_paid: true,
    last_paid: "2026-10-01",
    next_due: "2026-10-31",
    joined: "2025-01-01",
    last_login: "2026-10-05",
    notice: "VIP Member",
    open_invoices: 0,
    is_main: true,
  },
  {
    id: 2,
    name: "Jane Smith",
    owner_id: 202,
    owner_name: "Alpha Alliance",
    owner_type: "alliance",
    owner_logo: "https://images.evetech.net/alliances/202/logo",
    character_id: 2002,
    character_name: "Jane Smith",
    character_portrait: "https://images.evetech.net/characters/2002/portrait",
    status: "overdue",
    status_display: "Overdue",
    deposit: -5000000,
    tax_amount: 20000000,
    tax_period: 30,
    has_paid: false,
    last_paid: null,
    next_due: "2026-09-15",
    joined: "2024-06-01",
    last_login: null,
    notice: null,
    open_invoices: 2,
    is_main: false,
  },
];

const renderPage = (initialEntries = ["/taxsystem/account/"]) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={initialEntries}>
        <NuqsTestingAdapter>
          <AccountOverviewPage />
        </NuqsTestingAdapter>
      </MemoryRouter>
    </QueryClientProvider>,
  );
};

describe("AccountOverviewPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should show loading spinner initially", async () => {
    // Test Data
    vi.mocked(ApiCalls.loadUserAccounts).mockReturnValue(new Promise(() => {}));

    // Test Action
    renderPage();

    // Expected Result
    expect(screen.getByText("Loading account details...")).toBeInTheDocument();
  });

  it("should render account cards with status badges and metrics", async () => {
    // Test Data
    vi.mocked(ApiCalls.loadUserAccounts).mockResolvedValue(mockAccounts);

    // Test Action
    renderPage();

    // Expected Result
    await waitFor(() => {
      expect(screen.getByText("Mega Corp")).toBeInTheDocument();
      expect(screen.getByText("Alpha Alliance")).toBeInTheDocument();
    });

    expect(screen.getByText("Paid")).toBeInTheDocument();
    expect(screen.getByText("Unpaid / Due")).toBeInTheDocument();
    expect(screen.getByText("VIP Member")).toBeInTheDocument();
    expect(screen.getByText("2 Open")).toBeInTheDocument();
  });

  it("should filter accounts when search term is entered", async () => {
    // Test Data
    const user = userEvent.setup();
    vi.mocked(ApiCalls.loadUserAccounts).mockResolvedValue(mockAccounts);

    // Test Action
    renderPage();
    await waitFor(() => expect(screen.getByText("Mega Corp")).toBeInTheDocument());

    const searchInput = screen.getByPlaceholderText("Filter accounts by character or owner...");
    await user.type(searchInput, "Alpha");

    // Expected Result
    await waitFor(() => {
      expect(screen.getByText("Alpha Alliance")).toBeInTheDocument();
      expect(screen.queryByText("Mega Corp")).not.toBeInTheDocument();
    });
  });

  it("should filter accounts when owner type filter button is clicked", async () => {
    // Test Data
    const user = userEvent.setup();
    vi.mocked(ApiCalls.loadUserAccounts).mockResolvedValue(mockAccounts);

    // Test Action
    renderPage();
    await waitFor(() => expect(screen.getByText("Mega Corp")).toBeInTheDocument());

    const corpButton = screen.getByRole("button", { name: /Corporations/i });
    await user.click(corpButton);

    // Expected Result
    await waitFor(() => {
      expect(screen.getByText("Mega Corp")).toBeInTheDocument();
      expect(screen.queryByText("Alpha Alliance")).not.toBeInTheDocument();
    });
  });

  it("should display empty state when no accounts match query", async () => {
    // Test Data
    const user = userEvent.setup();
    vi.mocked(ApiCalls.loadUserAccounts).mockResolvedValue(mockAccounts);

    // Test Action
    renderPage();
    await waitFor(() => expect(screen.getByText("Mega Corp")).toBeInTheDocument());

    const searchInput = screen.getByPlaceholderText("Filter accounts by character or owner...");
    await user.type(searchInput, "NonexistentName");

    // Expected Result
    await waitFor(() => {
      expect(screen.getByText("No tax accounts found")).toBeInTheDocument();
      expect(screen.getByText("No accounts match your search query.")).toBeInTheDocument();
    });
  });

  it("should show error alert on api failure", async () => {
    // Test Data
    vi.mocked(ApiCalls.loadUserAccounts).mockRejectedValue(new Error("Network Error"));

    // Test Action
    renderPage();

    // Expected Result
    expect(await screen.findByText("Network Error")).toBeInTheDocument();
  });
});
