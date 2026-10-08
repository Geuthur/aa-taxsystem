// Third Party
import type { TFunction } from "i18next";
import { describe, expect, it, vi } from "vitest";

// AA TaxSystem
import {
  getAccountColumns,
  getAltColumns,
  getFilterRuleColumns,
  getFilterSetColumns,
  getGroupColumns,
  getHistoryColumns,
  getPaymentColumns,
} from "@/Components/Tables";

describe("Centralized Table Column Factories", () => {
  const mockT = ((key: string) => key) as unknown as TFunction;

  it("getPaymentColumns generates expected column ids", () => {
    // Test Data
    const renderActions = vi.fn();

    // Test Action
    const columnsWithChar = getPaymentColumns({
      t: mockT,
      showCharacter: true,
      showReviser: true,
      renderActions,
    });
    const columnsWithoutChar = getPaymentColumns({
      t: mockT,
      showCharacter: false,
    });

    // Expected Result
    expect(columnsWithChar.map((c) => c.id)).toEqual([
      "character",
      "date",
      "amount",
      "division",
      "status",
      "reason",
      "reviser",
      "actions",
    ]);
    expect(columnsWithoutChar.map((c) => c.id)).toEqual([
      "date",
      "amount",
      "division",
      "status",
      "reason",
    ]);
  });

  it("getAccountColumns generates expected column ids", () => {
    // Test Data
    const options = {
      t: mockT,
      onHistory: vi.fn(),
      onAddPayment: vi.fn(),
      onSwitchStatus: vi.fn(),
    };

    // Test Action
    const columns = getAccountColumns(options);

    // Expected Result
    expect(columns.map((c) => c.id)).toEqual([
      "character",
      "status",
      "deposit",
      "has_paid",
      "next_due",
      "actions",
    ]);
  });

  it("getAltColumns generates expected column ids", () => {
    // Test Data / Action
    const columns = getAltColumns({ t: mockT });

    // Expected Result
    expect(columns.map((c) => c.id)).toEqual(["character", "corporation"]);
  });

  it("getGroupColumns generates expected column ids", () => {
    // Test Data / Action
    const columns = getGroupColumns({ t: mockT, onDelete: vi.fn() });

    // Expected Result
    expect(columns.map((c) => c.id)).toEqual(["name", "groups", "actions"]);
  });

  it("getFilterSetColumns and getFilterRuleColumns generate expected column ids", () => {
    // Test Data / Action
    const setCols = getFilterSetColumns({
      t: mockT,
      activeSetId: 1,
      onSelect: vi.fn(),
      onDelete: vi.fn(),
    });
    const ruleCols = getFilterRuleColumns({
      t: mockT,
      filterTypeLabels: {},
      matchTypeLabels: {},
      onDelete: vi.fn(),
    });

    // Expected Result
    expect(setCols.map((c) => c.id)).toEqual([
      "name",
      "description",
      "enabled",
      "actions",
    ]);
    expect(ruleCols.map((c) => c.id)).toEqual([
      "filter_set",
      "filter_type",
      "match_type",
      "value",
      "actions",
    ]);
  });

  it("getHistoryColumns generates expected column ids", () => {
    // Test Data / Action
    const columns = getHistoryColumns({ t: mockT });

    // Expected Result
    expect(columns.map((c) => c.id)).toEqual([
      "date",
      "user_name",
      "target",
      "action",
      "comment",
    ]);
  });
});
