// React
import { MemoryRouter } from "react-router";

// Third Party
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

// AA TaxSystem
import * as ApiCalls from "@/Api/ApiCalls";
import type { TaxOwnerSettingSchema } from "@/Api/schema";
import { SettingsPage } from "@/Pages/SettingsPage";

vi.mock("@/Api/ApiCalls", () => ({
  loadUserSettings: vi.fn(),
  updateUserSettings: vi.fn(),
  loadSettingsOwners: vi.fn(),
  triggerUpdateAllTaxOwners: vi.fn(),
  triggerOwnerUpdate: vi.fn(),
  deleteOwner: vi.fn(),
}));

const mockOwners: TaxOwnerSettingSchema[] = [
  {
    id: 1,
    owner_id: 1001,
    owner_type: "corporation",
    name: "Acme Corp",
    ticker: "ACME",
    icon: "https://images.evetech.net/corporations/1001/logo",
    status: "ok",
    is_active: true,
    tax_amount: 10000000,
    tax_period: 30,
    open_invoices: 0,
    last_sync: "2026-10-19T20:00:00Z",
    sections: [
      {
        section: "wallet_journal",
        section_name: "Wallet Journal",
        is_success: true,
        has_token_error: false,
      },
    ],
  },
];

const renderPage = () => {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={queryClient}>
      <MemoryRouter initialEntries={["/taxsystem/settings/"]}>
        <SettingsPage />
      </MemoryRouter>
    </QueryClientProvider>,
  );
};

describe("SettingsPage", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("should load the saved global notification preference", async () => {
    // Test Data
    vi.mocked(ApiCalls.loadUserSettings).mockResolvedValueOnce({
      disable_notifications: true,
    });
    vi.mocked(ApiCalls.loadSettingsOwners).mockResolvedValueOnce([]);

    // Test Action
    renderPage();

    // Expected Result
    expect(
      await screen.findByRole("switch", { name: "Disable all notifications" }),
    ).toBeChecked();
  });

  it("should save the global preference when the switch is enabled", async () => {
    // Test Data
    const user = userEvent.setup();
    vi.mocked(ApiCalls.loadUserSettings).mockResolvedValue({
      disable_notifications: false,
    });
    vi.mocked(ApiCalls.loadSettingsOwners).mockResolvedValue([]);
    vi.mocked(ApiCalls.updateUserSettings).mockResolvedValue({
      disable_notifications: true,
    });

    // Test Action
    renderPage();
    const toggle = await screen.findByRole("switch", {
      name: "Disable all notifications",
    });
    await user.click(toggle);

    // Expected Result
    expect(ApiCalls.updateUserSettings).toHaveBeenCalledWith(
      { disable_notifications: true },
      expect.any(Object),
    );
    await waitFor(() => expect(toggle).toBeChecked());
  });

  it("should render owners update status list", async () => {
    // Test Data
    vi.mocked(ApiCalls.loadUserSettings).mockResolvedValue({
      disable_notifications: false,
    });
    vi.mocked(ApiCalls.loadSettingsOwners).mockResolvedValue(mockOwners);

    // Test Action
    renderPage();

    // Expected Result
    expect(await screen.findByText("Owners Update Status")).toBeInTheDocument();
    expect(screen.getByText("Acme Corp")).toBeInTheDocument();
    expect(screen.getByText(/\[ACME\]/)).toBeInTheDocument();
    expect(screen.getAllByText("OK").length).toBeGreaterThan(0);
    expect(screen.getByText("Wallet Journal")).toBeInTheDocument();
  });

  it("should trigger Update All with force_refresh=false", async () => {
    // Test Data
    const user = userEvent.setup();
    vi.mocked(ApiCalls.loadUserSettings).mockResolvedValue({
      disable_notifications: false,
    });
    vi.mocked(ApiCalls.loadSettingsOwners).mockResolvedValue(mockOwners);
    vi.mocked(ApiCalls.triggerUpdateAllTaxOwners).mockResolvedValue({
      message: "Queued update for all owners.",
    });

    // Test Action
    renderPage();
    const updateAllBtn = await screen.findByRole("button", { name: /^Update All/i });
    await user.click(updateAllBtn);

    // Expected Result
    await waitFor(() => {
      expect(ApiCalls.triggerUpdateAllTaxOwners).toHaveBeenCalledWith(false);
    });
    expect(await screen.findByText("Queued update for all owners.")).toBeInTheDocument();
  });

  it("should trigger single owner update with force_refresh=false", async () => {
    // Test Data
    const user = userEvent.setup();
    vi.mocked(ApiCalls.loadUserSettings).mockResolvedValue({
      disable_notifications: false,
    });
    vi.mocked(ApiCalls.loadSettingsOwners).mockResolvedValue(mockOwners);
    vi.mocked(ApiCalls.triggerOwnerUpdate).mockResolvedValue({
      message: "Queued update for Acme Corp.",
    });

    // Test Action
    renderPage();
    const updateOwnerBtn = await screen.findByRole("button", { name: /^Update owner/i });
    await user.click(updateOwnerBtn);

    // Expected Result
    await waitFor(() => {
      expect(ApiCalls.triggerOwnerUpdate).toHaveBeenCalledWith({
        ownerId: 1001,
        forceRefresh: false,
      });
    });
    expect(await screen.findByText("Queued update for Acme Corp.")).toBeInTheDocument();
  });

  it("should open delete modal and call deleteOwner on confirm", async () => {
    // Test Data
    const user = userEvent.setup();
    vi.mocked(ApiCalls.loadUserSettings).mockResolvedValue({
      disable_notifications: false,
    });
    vi.mocked(ApiCalls.loadSettingsOwners).mockResolvedValue(mockOwners);
    vi.mocked(ApiCalls.deleteOwner).mockResolvedValue({
      message: "Corporation Acme Corp deleted successfully.",
    });

    // Test Action
    renderPage();
    const deleteBtn = await screen.findByRole("button", { name: /Delete Owner|Delete/i });
    await user.click(deleteBtn);

    // Expected Result
    expect(await screen.findByText("Delete Owner")).toBeInTheDocument();
    const confirmBtn = screen.getByRole("button", { name: /^Confirm Delete/i });
    await user.click(confirmBtn);

    await waitFor(() => {
      expect(ApiCalls.deleteOwner).toHaveBeenCalledWith(1001);
    });
    expect(await screen.findByText("Corporation Acme Corp deleted successfully.")).toBeInTheDocument();
  });
});
