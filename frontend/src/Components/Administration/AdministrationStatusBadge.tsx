// React
import type { KeyboardEvent } from "react";

// Third Party
import { Badge } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// AA TaxSystem
import styles from "@/Styles/modules/Administration.module.css";

export interface AdministrationStatusBadgeProps {
  /** Owner status as delivered by the API (e.g. "ok", "error", "token_error") */
  status: string;
  /** If set, the badge becomes a keyboard accessible button */
  onClick?: () => void;
  /** Accessible name used when the badge is clickable */
  ariaLabel?: string;
}

/** Status badge of an owner. Clickable (role="button") when `onClick` is given. */
export function AdministrationStatusBadge({
  status,
  onClick,
  ariaLabel,
}: AdministrationStatusBadgeProps) {
  const { t } = useTranslation();

  let bg = "secondary";
  let text: "dark" | undefined;
  let label: string = status;

  switch (status.toLowerCase()) {
    case "ok":
      bg = "success";
      label = t("OK");
      break;
    case "error":
      bg = "danger";
      label = t("Error");
      break;
    case "token_error":
      bg = "warning";
      text = "dark";
      label = t("Token Error");
      break;
    case "incomplete":
      bg = "warning";
      text = "dark";
      label = t("Incomplete");
      break;
    case "in_progress":
      bg = "info";
      label = t("In Progress");
      break;
    case "disabled":
      bg = "secondary";
      label = t("Disabled");
      break;
  }

  if (!onClick) {
    return (
      <Badge bg={bg} text={text}>
        {label}
      </Badge>
    );
  }

  const handleKeyDown = (event: KeyboardEvent<HTMLElement>) => {
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      onClick();
    }
  };

  return (
    <Badge
      bg={bg}
      text={text}
      role="button"
      tabIndex={0}
      aria-label={ariaLabel}
      className={styles.cursorPointer}
      onClick={onClick}
      onKeyDown={handleKeyDown}
    >
      {label}
    </Badge>
  );
}

export default AdministrationStatusBadge;
