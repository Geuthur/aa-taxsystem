// React
import type { ReactNode } from "react";

// Third Party
import { Button } from "react-bootstrap";

export interface ButtonGroupFilterOption<T extends string = string> {
  value: T;
  label: string;
  icon?: ReactNode;
  activeVariant?: string;
  inactiveVariant?: string;
}

export interface ButtonGroupFilterProps<T extends string = string> {
  value: T;
  onChange: (value: T) => void;
  options: ButtonGroupFilterOption<T>[];
  size?: "sm" | "lg";
  className?: string;
  ariaLabel?: string;
}

export function ButtonGroupFilter<T extends string = string>({
  value,
  onChange,
  options,
  size = "sm",
  className = "",
  ariaLabel,
}: ButtonGroupFilterProps<T>) {
  return (
    <div
      className={`btn-group ${className}`.trim()}
      role="group"
      aria-label={ariaLabel}
    >
      {options.map((opt) => {
        const isActive = value === opt.value;
        const activeClass = opt.activeVariant || "aa-btn-primary";
        const inactiveClass = opt.inactiveVariant || "aa-btn-secondary";
        const btnVariantClass = isActive ? activeClass : inactiveClass;

        return (
          <Button
            key={opt.value}
            className={`aa-btn aa-btn-${size} ${btnVariantClass} d-inline-flex align-items-center gap-1`}
            onClick={() => onChange(opt.value)}
          >
            {opt.icon}
            <span>{opt.label}</span>
          </Button>
        );
      })}
    </div>
  );
}

export default ButtonGroupFilter;
