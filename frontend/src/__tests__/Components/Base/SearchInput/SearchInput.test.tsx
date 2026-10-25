// Third Party
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

// AA TaxSystem
// AA Tax System
import { SearchInput } from "@/Components/Base/SearchInput";

describe("SearchInput", () => {
  it("should show the value and the placeholder as label", () => {
    // Test Data
    const placeholder = "Filter members by name…";

    // Test Action
    render(<SearchInput value="Alpha" onChange={vi.fn()} placeholder={placeholder} />);

    // Expected Result
    expect(screen.getByRole("textbox", { name: placeholder })).toHaveValue("Alpha");
  });

  it("should call onChange with the typed text", async () => {
    // Test Data
    const user = userEvent.setup();
    const onChange = vi.fn();
    render(<SearchInput value="" onChange={onChange} placeholder="Search" />);

    // Test Action
    await user.type(screen.getByRole("textbox", { name: "Search" }), "a");

    // Expected Result
    expect(onChange).toHaveBeenCalledWith("a");
  });
});
