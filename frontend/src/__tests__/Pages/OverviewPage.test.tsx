// React
import { MemoryRouter, Route, Routes } from "react-router-dom";

// Third Party
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NuqsTestingAdapter } from "nuqs/adapters/testing";
import { beforeEach, describe, expect, it, vi } from "vitest";

// AA TaxSystem
import * as ApiCalls from "@/Api/ApiCalls";
import type { components } from "@/Api/OpenApi";
import { OverviewPage } from "@/Pages/OverviewPage";

type OverviewSchema = components["schemas"]["OverviewSchema"];

vi.mock("@/Api/ApiCalls", async (importOriginal) => {
  const actual = await importOriginal<typeof import("@/Api/ApiCalls")>();
  return {
    ...actual,
    loadOverview: vi.fn(),
  };
});

const mockOverview: OverviewSchema = {
  total_count: 2,
  owners: [
    {
      id: 101,
      name: "Corp One",
      type: "corporation",
      type_display: "Corporation",
      portrait_url: "https://images.evetech.net/corporations/101/logo",
      active: true,
      open_invoices: 2,
      can_manage: true,
      has_errors: false,
    },
    {
      id: 201,
      name: "Alliance One",
      type: "alliance",
      type_display: "Alliance",
      portrait_url: "https://images.evetech.net/alliances/201/logo",
      active: true,
      open_invoices: 0,
      can_manage: true,
      has_errors: true,
    },
  ],
};

const renderPage = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <NuqsTestingAdapter>
        <MemoryRouter initialEntries={["/taxsystem/"]}>
          <Routes>
            <Route path="/taxsystem/" element={<OverviewPage />} />
          </Routes>
        </MemoryRouter>
      </NuqsTestingAdapter>
    </QueryClientProvider>,
  );
};

describe("OverviewPage in aa-taxsystem", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("renders overview cards for corporations and alliances", async () => {
    // Test Data
    vi.mocked(ApiCalls.loadOverview).mockResolvedValue(mockOverview);

    // Test Action
    renderPage();

    // Expected Result
    expect(await screen.findByText("Corp One")).toBeInTheDocument();
    expect(screen.getByText("Alliance One")).toBeInTheDocument();
    expect(screen.getByText("2 Owners")).toBeInTheDocument();
  });

  it("filters owners using search input", async () => {
    // Test Data
    vi.mocked(ApiCalls.loadOverview).mockResolvedValue(mockOverview);
    const user = userEvent.setup();

    // Test Action
    renderPage();
    await screen.findByText("Corp One");
    const searchInput = screen.getByPlaceholderText(/search corporations & alliances/i);
    await user.type(searchInput, "Alliance");

    // Expected Result
    expect(screen.getByText("Alliance One")).toBeInTheDocument();
    expect(screen.queryByText("Corp One")).not.toBeInTheDocument();
  });

  it("renders pulsing indicator on Manage button when owner has errors", async () => {
    // Test Data
    vi.mocked(ApiCalls.loadOverview).mockResolvedValue(mockOverview);

    // Test Action
    renderPage();
    await screen.findByText("Alliance One");

    // Expected Result - Alliance One has has_errors: true
    const manageLinks = screen.getAllByRole("link", { name: /manage/i });
    expect(manageLinks).toHaveLength(2);

    // First card (Corp One) has has_errors: false
    expect(manageLinks[0]).not.toHaveClass("aa-btn-pulse");
    expect(manageLinks[0].querySelector(".aa-pending-dot-container")).toBeNull();

    // Second card (Alliance One) has has_errors: true
    expect(manageLinks[1]).toHaveClass("aa-btn-pulse");
    expect(manageLinks[1].querySelector(".aa-pending-dot-container")).toBeInTheDocument();
  });
});
