// React
import { MemoryRouter } from "react-router";

// Third Party
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { NuqsTestingAdapter } from "nuqs/adapters/testing";
import { describe, expect, it, vi } from "vitest";

// AA TaxSystem
import type { AdministrationTaxOwnerSchema } from "@/Api/schema";
import { AdministrationOwnersTable } from "@/Components/Administration";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({ t: (key: string) => key }),
}));

const buildOwner = (
  overrides: Partial<AdministrationTaxOwnerSchema> = {},
): AdministrationTaxOwnerSchema => ({
  id: 1,
  owner_id: 101,
  owner_type: "corporation",
  name: "Alpha Mining Corp",
  icon: "",
  ticker: "AMC",
  status: "ok",
  is_active: true,
  tax_amount: 1000,
  tax_period: 30,
  open_invoices: 0,
  last_sync: null,
  error_message: null,
  ...overrides,
});

const renderTable = (data: AdministrationTaxOwnerSchema[]) =>
  render(
    <MemoryRouter>
      <NuqsTestingAdapter>
        <AdministrationOwnersTable
          data={data}
          isLoading={false}
          onInspect={vi.fn()}
          onUpdate={vi.fn()}
          onDelete={vi.fn()}
        />
      </NuqsTestingAdapter>
    </MemoryRouter>,
  );

describe("AdministrationOwnersTable status badge", () => {
  it("should render a clickable badge when owner has an error message", () => {
    // Test Data
    renderTable([buildOwner({ status: "error", error_message: "ESI Token Expired" })]);

    // Test Action
    const badge = screen.getByRole("button", { name: /show error details/i });

    // Expected Result
    expect(badge).toHaveTextContent("Error");
    expect(badge).toHaveAttribute("tabindex", "0");
    expect(screen.queryByText("ESI Token Expired")).not.toBeInTheDocument();
  });

  it("should open the modal with the full message when badge is clicked", async () => {
    // Test Data
    const user = userEvent.setup();
    renderTable([buildOwner({ status: "error", error_message: "ESI Token Expired" })]);

    // Test Action
    await user.click(screen.getByRole("button", { name: /show error details/i }));

    // Expected Result
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByText("ESI Token Expired")).toBeInTheDocument();
  });

  it("should open the modal when Enter is pressed on the focused badge", async () => {
    // Test Data
    const user = userEvent.setup();
    renderTable([buildOwner({ status: "error", error_message: "Boom" })]);

    // Test Action
    screen.getByRole("button", { name: /show error details/i }).focus();
    await user.keyboard("{Enter}");

    // Expected Result
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    expect(screen.getByText("Boom")).toBeInTheDocument();
  });

  it("should not make the badge clickable when owner has no error", async () => {
    // Test Data
    const user = userEvent.setup();
    renderTable([buildOwner({ status: "ok" })]);

    // Test Action
    await user.click(screen.getByText("OK"));

    // Expected Result
    expect(screen.queryByRole("button", { name: /show error details/i })).not.toBeInTheDocument();
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("should show the default text for token_error without message", async () => {
    // Test Data
    const user = userEvent.setup();
    renderTable([buildOwner({ status: "token_error", error_message: null })]);

    // Test Action
    await user.click(screen.getByRole("button", { name: /show error details/i }));

    // Expected Result
    expect(
      screen.getByText(
        "The ESI token is invalid or expired. Re-add the character or corporation.",
      ),
    ).toBeInTheDocument();
  });
});
