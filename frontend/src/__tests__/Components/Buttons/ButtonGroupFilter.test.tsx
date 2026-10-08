// Third Party
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

// AA TaxSystem
import { ButtonGroupFilter } from "@/Components/Buttons/ButtonGroupFilter";

describe("ButtonGroupFilter Component", () => {
  it("renders all options and calls onChange when clicked", async () => {
    // Test Data
    const handleChange = vi.fn();
    const options = [
      { value: "all", label: "All Options" },
      { value: "paid", label: "Paid Only", activeVariant: "aa-btn-success" },
      { value: "unpaid", label: "Unpaid Only", activeVariant: "aa-btn-danger" },
    ];

    // Test Action
    render(
      <ButtonGroupFilter
        value="all"
        onChange={handleChange}
        options={options}
        ariaLabel="Filter Test Group"
      />,
    );

    const paidBtn = screen.getByRole("button", { name: "Paid Only" });
    await userEvent.click(paidBtn);

    // Expected Result
    expect(screen.getByRole("button", { name: "All Options" })).toBeInTheDocument();
    expect(paidBtn).toBeInTheDocument();
    expect(handleChange).toHaveBeenCalledWith("paid");
  });

  it("applies activeVariant styling to the selected option", () => {
    // Test Data
    const options = [
      { value: "all", label: "All" },
      { value: "paid", label: "Paid", activeVariant: "aa-btn-success" },
    ];

    // Test Action
    render(
      <ButtonGroupFilter
        value="paid"
        onChange={() => {}}
        options={options}
      />,
    );

    // Expected Result
    const paidBtn = screen.getByRole("button", { name: "Paid" });
    expect(paidBtn.className).toContain("aa-btn-success");
  });
});
