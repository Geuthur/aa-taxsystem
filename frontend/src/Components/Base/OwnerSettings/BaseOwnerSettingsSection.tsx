// React
import { useState } from "react";

// Third Party
import { AlertTriangle, RotateCw, Trash2, Users } from "lucide-react";
import { Alert, Button, Card } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// AA TaxSystem
// AA Base
import { BaseModal } from "@/Components/Base/BaseModal";
import { BaseOwnerCard } from "@/Components/Base/OwnerSettings/BaseOwnerCard";
import { MissingOwnerCard } from "@/Components/Base/OwnerSettings/MissingOwnerCard";
import styles from "@/Components/Base/OwnerSettings/OwnerSettings.module.css";
import type {
  BaseMissingOwner,
  BaseOwner,
  BaseOwnerSettingsSectionProps,
} from "@/Components/Base/OwnerSettings/types";

/**
 * Reusable owner overview for the Settings page: header with "Update All", feedback alert,
 * owner grid, missing (unregistered) owners and the delete confirmation modal.
 * Project specific parts are injected via renderCustomCardContent / renderCardActions.
 */
export function BaseOwnerSettingsSection<
  T extends BaseOwner = BaseOwner,
  M extends BaseMissingOwner = BaseMissingOwner,
>({
  title,
  description,
  icon,
  owners,
  missingOwners,
  isLoading = false,
  isError = false,
  errorMessage,
  emptyMessage,
  appName = "Alliance Auth",
  onUpdateAll,
  isUpdatingAll = false,
  globalCooldown = 0,
  feedbackMessage,
  onDismissFeedback,
  onTriggerSingleUpdate,
  updatingOwnerId = null,
  ownerCooldowns = {},
  onDeleteOwner,
  isDeleting = false,
  deleteModalTitle,
  deleteModalDescription,
  renderCustomCardContent,
  renderCardActions,
  missingSectionTitle,
  missingActionUrl,
  missingActionLabel,
}: BaseOwnerSettingsSectionProps<T, M>) {
  const { t } = useTranslation();
  const [ownerToDelete, setOwnerToDelete] = useState<T | null>(null);

  const hasOwners = (owners?.length ?? 0) > 0;
  const hasMissing = (missingOwners?.length ?? 0) > 0;

  const handleDeleteConfirm = async () => {
    if (ownerToDelete && onDeleteOwner) {
      await onDeleteOwner(ownerToDelete);
      setOwnerToDelete(null);
    }
  };

  return (
    <Card className={`${styles["section"]} border-0`}>
      <Card.Body className="bg-secondary text-light">
        <Card.Header
          className={`${styles["section-header"]} bg-secondary d-flex justify-content-between align-items-center flex-wrap gap-2`}
        >
          <div>
            <div className={styles["section-title-wrap"]}>
              {icon ?? <Users size={20} aria-hidden="true" />}
              <h2 className={styles["section-title"]}>{title ?? t("Owner Status")}</h2>
              {owners && <span className={styles["section-count"]}>({owners.length})</span>}
            </div>
            <p className={styles["section-description"]}>
              {description ?? t("ESI synchronization status of your linked owners.")}
            </p>
          </div>

          {onUpdateAll && hasOwners && (
            <Button
              variant="secondary"
              size="sm"
              className="aa-btn aa-btn-secondary aa-btn-sm d-flex align-items-center gap-1"
              disabled={isUpdatingAll || globalCooldown > 0}
              onClick={onUpdateAll}
            >
              {isUpdatingAll ? (
                <span className="spinner-border spinner-border-sm" />
              ) : (
                <RotateCw size={14} />
              )}
              <span>
                {globalCooldown > 0
                  ? t("Update All ({{seconds}}s)", { seconds: globalCooldown })
                  : t("Update All")}
              </span>
            </Button>
          )}
        </Card.Header>

        {feedbackMessage && (
          <Alert
            variant={feedbackMessage.variant}
            className="py-2 mb-3"
            dismissible={Boolean(onDismissFeedback)}
            onClose={onDismissFeedback}
          >
            {feedbackMessage.text}
          </Alert>
        )}

        {isLoading && (
          <div className="aa-loader-container">
            <span className="spinner-border" />
            <span>{t("Loading update statuses…")}</span>
          </div>
        )}

        {isError && (
          <Card className="bg-secondary border-0 shadow-sm" role="alert">
            <Card.Body className={styles["error"]}>
              {errorMessage ?? t("Failed to load update status.")}
            </Card.Body>
          </Card>
        )}

        {!isLoading && !isError && !hasOwners && !hasMissing && (
          <Card className="bg-secondary text-light border-0 shadow-sm">
            <Card.Body className={styles["empty-state"]}>
              {emptyMessage ?? t("Nothing to show.")}
            </Card.Body>
          </Card>
        )}

        {!isLoading && !isError && hasOwners && (
          <div className={styles["characters-grid"]}>
            {owners?.map((owner) => (
              <BaseOwnerCard<T>
                key={owner.id}
                owner={owner}
                isUpdating={updatingOwnerId === owner.id}
                cooldown={ownerCooldowns[owner.id] ?? 0}
                onTriggerUpdate={onTriggerSingleUpdate}
                onDeleteClick={onDeleteOwner ? setOwnerToDelete : undefined}
                renderCustomContent={renderCustomCardContent}
                renderActions={renderCardActions}
              />
            ))}
          </div>
        )}

        {!isLoading && !isError && hasMissing && (
          <div className="mt-4">
            <h3 className="h6 text-muted mb-3">
              {missingSectionTitle ?? t("Not registered in {{app}}", { app: appName })} (
              {missingOwners?.length})
            </h3>
            <div className={styles["characters-grid"]}>
              {missingOwners?.map((missing) => (
                <MissingOwnerCard
                  key={missing.id}
                  missing={missing}
                  appName={appName}
                  actionUrl={missingActionUrl}
                  actionLabel={missingActionLabel}
                />
              ))}
            </div>
          </div>
        )}

        {onDeleteOwner && (
          <BaseModal
            show={Boolean(ownerToDelete)}
            onHide={() => !isDeleting && setOwnerToDelete(null)}
            centered
            title={
              <div className="d-flex align-items-center gap-2 text-danger">
                <Trash2 size={20} />
                <span>{deleteModalTitle ?? t("Delete Owner")}</span>
              </div>
            }
            footer={
              <div className="d-flex align-items-center justify-content-end gap-2 w-100">
                <Button
                  variant="secondary"
                  onClick={() => setOwnerToDelete(null)}
                  disabled={isDeleting}
                  className="aa-btn aa-btn-secondary"
                >
                  {t("Cancel")}
                </Button>
                <Button
                  variant="danger"
                  onClick={handleDeleteConfirm}
                  disabled={isDeleting}
                  className="aa-btn aa-btn-danger d-flex align-items-center gap-1"
                >
                  <Trash2 size={14} />
                  <span>{isDeleting ? t("Deleting…") : t("Confirm Delete")}</span>
                </Button>
              </div>
            }
          >
            <div className="p-3 d-flex align-items-start gap-3">
              <AlertTriangle className="text-danger flex-shrink-0 mt-1" size={24} />
              <div>
                <p className="fw-semibold mb-1">
                  {t("Are you sure you want to delete owner '{{name}}'?", {
                    name: ownerToDelete?.name,
                  })}
                </p>
                <div className="small text-muted">
                  {ownerToDelete && deleteModalDescription
                    ? deleteModalDescription(ownerToDelete)
                    : t("This action cannot be undone.")}
                </div>
              </div>
            </div>
          </BaseModal>
        )}
      </Card.Body>
    </Card>
  );
}
