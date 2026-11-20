// Third Party
import { render, screen } from "@testing-library/react";
import type { TFunction } from "i18next";
import { describe, expect, it, vi } from "vitest";

// AA TaxSystem
import { getAccountColumns, isAccountUnpaid } from "@/Components/Tables";
import type { AccountRow } from "@/Components/Tables";

const mockT = ((key: string) => key) as unknown as TFunction;

const makeAccount = (overrides: Partial<AccountRow> = {}): AccountRow => ({
  account_id: 1,
  account: {
    character_id: 2001,
    character_name: "John Doe",
    character_portrait: "https://images.evetech.net/characters/2001/portrait",
    alt_ids: [],
  },
  status: "Active",
  deposit: 0,
  has_paid: false,
  is_tax_free: false,
  last_paid: null,
  next_due: null,
  is_active: true,
  open_invoices: 0,
  ...overrides,
});

const renderPaidCell = (account: AccountRow) => {
  const columns = getAccountColumns({
    t: mockT,
    onHistory: vi.fn(),
    onAddPayment: vi.fn(),
    onSwitchStatus: vi.fn(),
  });
  const column = columns.find((c) => c.id === "has_paid");
  const cell = column?.cell as (ctx: unknown) => React.ReactNode;
  return render(<>{cell({ getValue: () => account.has_paid, row: { original: account } })}</>);
};

describe("accountColumns", () => {
  it("should show the tax-free badge instead of unpaid for a tax-free account", () => {
    // Test Action
    renderPaidCell(makeAccount({ has_paid: false, is_tax_free: true }));

    // Expected Result
    expect(screen.getByText("Tax-Free")).toBeInTheDocument();
    expect(screen.queryByText("Unpaid")).not.toBeInTheDocument();
    expect(screen.queryByText("Paid")).not.toBeInTheDocument();
  });

  it("should show unpaid for a taxed account that has not paid", () => {
    // Test Action
    renderPaidCell(makeAccount({ has_paid: false }));

    // Expected Result
    expect(screen.getByText("Unpaid")).toBeInTheDocument();
    expect(screen.queryByText("Tax-Free")).not.toBeInTheDocument();
  });

  it("should show paid for a taxed account that has paid", () => {
    // Test Action
    renderPaidCell(makeAccount({ has_paid: true }));

    // Expected Result
    expect(screen.getByText("Paid")).toBeInTheDocument();
  });

  it("isAccountUnpaid should exclude tax-free accounts", () => {
    // Expected Result
    expect(isAccountUnpaid(makeAccount({ has_paid: false }))).toBe(true);
    expect(isAccountUnpaid(makeAccount({ has_paid: false, is_tax_free: true }))).toBe(false);
    expect(isAccountUnpaid(makeAccount({ has_paid: true }))).toBe(false);
  });
});
