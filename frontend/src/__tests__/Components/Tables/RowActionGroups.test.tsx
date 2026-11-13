// Third Party
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import type { TFunction } from "i18next";
import { describe, expect, it, vi } from "vitest";

// AA TaxSystem
import { getAccountColumns, getGroupColumns } from "@/Components/Tables";

const mockT = ((key: string) => key) as unknown as TFunction;

function renderActions(column: { cell?: unknown }, original: unknown) {
  const cell = column.cell as (ctx: { row: { original: unknown } }) => React.ReactNode;
  return render(<>{cell({ row: { original } })}</>);
}

describe("Row action button groups", () => {
  it("renders account actions as icon-only buttons in one ButtonGroup", async () => {
    // Test Data
    const onHistory = vi.fn();
    const onAddPayment = vi.fn();
    const onSwitchStatus = vi.fn();
    const onReset = vi.fn();
    const columns = getAccountColumns({ t: mockT, onHistory, onAddPayment, onSwitchStatus, onReset });
    const actions = columns.find((c) => c.id === "actions")!;
    const user = userEvent.setup();

    // Test Action
    const { container } = renderActions(actions, { status: "active" });
    await user.click(screen.getByRole("button", { name: "History" }));
    await user.click(screen.getByRole("button", { name: "Reset" }));

    // Expected Result
    const group = container.querySelector(".btn-group.btn-group-sm");
    expect(group).not.toBeNull();
    expect(group!.querySelectorAll("button")).toHaveLength(4);
    expect(onHistory).toHaveBeenCalledTimes(1);
    expect(onReset).toHaveBeenCalledTimes(1);
  });

  it("renders the group delete action in a ButtonGroup", async () => {
    // Test Data
    const onDelete = vi.fn();
    const columns = getGroupColumns({ t: mockT, onDelete });
    const actions = columns.find((c) => c.id === "actions")!;
    const user = userEvent.setup();

    // Test Action
    const { container } = renderActions(actions, { id: 1, name: "G" });
    await user.click(screen.getByRole("button", { name: "Delete" }));

    // Expected Result
    expect(container.querySelector(".btn-group.btn-group-sm")).not.toBeNull();
    expect(onDelete).toHaveBeenCalledTimes(1);
  });
});
