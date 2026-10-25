// React
import type { ReactNode } from "react";

// Third Party
import { Badge, Button } from "react-bootstrap";

export interface ButtonGroupFilterOption<T extends string = string> {
  value: T;
  label: string;
  icon?: ReactNode;
  /** Optional counter shown as a badge after the label. */
  count?: number;
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
        const variant = isActive ? opt.activeVariant || "primary" : opt.inactiveVariant || "secondary";

        return (
          <Button
            key={opt.value}
            variant={variant}
            size={size}
            className="d-inline-flex align-items-center gap-1"
            aria-pressed={isActive}
            onClick={() => onChange(opt.value)}
          >
            {opt.icon}
            <span>{opt.label}</span>
            {opt.count !== undefined && (
              <>
                {" "}
                <Badge bg="secondary" className="ms-1">
                  {opt.count}
                </Badge>
              </>
            )}
          </Button>
        );
      })}
    </div>
  );
}

export default ButtonGroupFilter;
