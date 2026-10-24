// Third Party
import { useTranslation } from "react-i18next";

// AA TaxSystem
import { AdministrationStatusBadge } from "@/Components/Administration/AdministrationStatusBadge";
import { BaseModal } from "@/Components/Base/BaseModal";

export interface AdministrationErrorModalProps {
  show: boolean;
  onHide: () => void;
  ownerName: string;
  status: string;
  /** Full error message; a default text is shown for `token_error` without one */
  errorMessage?: string | null;
}

/** Shows the full error message of an owner (opened from the status badge). */
export function AdministrationErrorModal({
  show,
  onHide,
  ownerName,
  status,
  errorMessage,
}: AdministrationErrorModalProps) {
  const { t } = useTranslation();

  const message =
    errorMessage ||
    (status.toLowerCase() === "token_error"
      ? t(
          "The ESI token is invalid or expired. Re-add the character or corporation."
        )
      : t("No error message available."));

  return (
    <BaseModal show={show} onHide={onHide} title={t("Error details")}>
      <div className="d-flex align-items-center gap-2 mb-3">
        <span className="fw-semibold">{ownerName}</span>
        <AdministrationStatusBadge status={status} />
      </div>
      <pre className="text-break text-wrap mb-0">{message}</pre>
    </BaseModal>
  );
}

export default AdministrationErrorModal;
