// React
import { MemoryRouter } from "react-router-dom";

// Third Party
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { useUserSettings } from "aa-geuthur-react";
import { beforeEach, describe, expect, it, vi } from "vitest";

// AA TaxSystem
import * as ApiCalls from "@/Api/ApiCalls";
import type { TaxOwnerSettingSchema } from "@/Api/schema";
import { SettingsPage } from "@/Pages/SettingsPage";

// The hook itself (request, optimistic update, rollback) is tested in aa-geuthur-react.
vi.mock("aa-geuthur-react", async (importOriginal) => {
  const actual = await importOriginal<typeof import("aa-geuthur-react")>();
  return { ...actual, useUserSettings: vi.fn() };
});

vi.mock("@/Api/ApiCalls", () => ({
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

type HookResult = ReturnType<typeof useUserSettings>;

const mutate = vi.fn();

/** Sets what `useUserSettings` returns for the page. */
const mockSettings = (result: object, mutation: object = {}) => {
  vi.mocked(useUserSettings).mockReturnValue({
    data: undefined,
    isLoading: false,
    isError: false,
    ...result,
    updateMutation: { mutate, isError: false, isPending: false, ...mutation },
  } as unknown as HookResult);
};

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
    mockSettings({ data: { disable_notifications: true } });
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
    mockSettings({ data: { disable_notifications: false } });
    vi.mocked(ApiCalls.loadSettingsOwners).mockResolvedValue([]);

    // Test Action
    renderPage();
    await user.click(await screen.findByRole("switch", { name: "Disable all notifications" }));

    // Expected Result
    expect(mutate).toHaveBeenCalledWith({ disable_notifications: true });
  });

  it("should show the loader while the settings load", () => {
    // Test Data
    mockSettings({ isLoading: true });
    vi.mocked(ApiCalls.loadSettingsOwners).mockResolvedValue([]);

    // Test Action
    renderPage();

    // Expected Result
    expect(screen.getByText("Loading settings…")).toBeInTheDocument();
    expect(screen.queryByRole("switch")).not.toBeInTheDocument();
  });

  it("should show an error when the settings cannot be loaded", () => {
    // Test Data
    mockSettings({ isError: true });
    vi.mocked(ApiCalls.loadSettingsOwners).mockResolvedValue([]);

    // Test Action
    renderPage();

    // Expected Result
    expect(screen.getByRole("alert")).toHaveTextContent("Failed to load settings. Please try refreshing the page.");
  });

  it("should tell the user when saving failed", () => {
    // Test Data
    mockSettings({ data: { disable_notifications: false } }, { isError: true });
    vi.mocked(ApiCalls.loadSettingsOwners).mockResolvedValue([]);

    // Test Action
    renderPage();

    // Expected Result
    expect(screen.getByRole("alert")).toHaveTextContent(
      "Could not save this setting. Your previous preference was restored.",
    );
  });

  it("should keep the look of the owner section through the class props of the package", async () => {
    // Test Data
    const user = userEvent.setup();
    mockSettings({ data: { disable_notifications: false } });
    vi.mocked(ApiCalls.loadSettingsOwners).mockResolvedValue(mockOwners);

    // Test Action
    const { container } = renderPage();
    const card = (await screen.findByText("Acme Corp")).closest("article");
    await user.click(screen.getByRole("button", { name: "Delete Owner" }));

    // Expected Result
    expect(card).toHaveClass("aa-owner-card", "bg-dark");
    expect(container.querySelector(".card-body.bg-secondary.text-light")).toContainElement(card as HTMLElement);
    expect(document.querySelector(".modal-body")).toHaveClass("aa-panel");
    expect(screen.queryByRole("searchbox")).not.toBeInTheDocument();
  });

  it("should render owners update status list", async () => {
    // Test Data
    mockSettings({ data: { disable_notifications: false } });
    vi.mocked(ApiCalls.loadSettingsOwners).mockResolvedValue(mockOwners);

    // Test Action
    renderPage();

    // Expected Result
    expect(await screen.findByText("Owners Update Status")).toBeInTheDocument();
    expect(await screen.findByText("Acme Corp")).toBeInTheDocument();
    expect(screen.getByText(/\[ACME\]/)).toBeInTheDocument();
    expect(screen.getAllByText("OK").length).toBeGreaterThan(0);
    expect(screen.getByText("Wallet Journal")).toBeInTheDocument();
  });

  it("should trigger Update All with force_refresh=false", async () => {
    // Test Data
    const user = userEvent.setup();
    mockSettings({ data: { disable_notifications: false } });
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
    mockSettings({ data: { disable_notifications: false } });
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
    mockSettings({ data: { disable_notifications: false } });
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
