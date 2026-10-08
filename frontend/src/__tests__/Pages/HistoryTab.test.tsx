// React
import { MemoryRouter } from "react-router-dom";

// Third Party
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";

// AA TaxSystem
import * as ApiCalls from "@/Api/ApiCalls";
import type { components } from "@/Api/OpenApi";
import { HistoryTab } from "@/Pages/Manage/Tabs/HistoryTab";

type AdminLogRow = components["schemas"]["AdminHistorySchema"];

vi.mock("@/Api/ApiCalls", () => ({
  loadAdminLogs: vi.fn(),
}));

const mockLogs: AdminLogRow[] = [
  {
    log_id: 1,
    date: "2026-10-01 12:00",
    user_name: "Admin Alice",
    target: "Tax Account",
    action: "Added",
    action_display: "Added",
    comment: "Added account",
  },
  {
    log_id: 2,
    date: "2026-10-02 14:00",
    user_name: "Admin Bob",
    target: "Settings",
    action: "Changed",
    action_display: "Changed",
    comment: "Changed tax rate",
  },
  {
    log_id: 3,
    date: "2026-10-03 16:00",
    user_name: "Admin Charlie",
    target: "Filter",
    action: "Deleted",
    action_display: "Deleted",
    comment: "Deleted obsolete filter",
  },
];

const renderComponent = (ownerId = 98000001) => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter>
        <HistoryTab ownerId={ownerId} />
      </MemoryRouter>
    </QueryClientProvider>,
  );
};

describe("HistoryTab", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should render action badges with correct variant colors: green for added, yellow for changed, red for deleted", async () => {
    // Test Data
    vi.mocked(ApiCalls.loadAdminLogs).mockResolvedValue(mockLogs);

    // Test Action
    renderComponent();

    // Expected Result
    const addedBadge = await screen.findByText("Added");
    expect(addedBadge).toBeInTheDocument();
    expect(addedBadge).toHaveClass("bg-success");

    const changedBadge = await screen.findByText("Changed");
    expect(changedBadge).toBeInTheDocument();
    expect(changedBadge).toHaveClass("bg-warning");

    const deletedBadge = await screen.findByText("Deleted");
    expect(deletedBadge).toBeInTheDocument();
    expect(deletedBadge).toHaveClass("bg-danger");
  });
});
