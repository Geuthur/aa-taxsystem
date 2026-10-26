// React
import React, { useMemo } from "react";

// Third Party
import { BellOff, Settings2, Users } from "lucide-react";
import { Card } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// AA TaxSystem
import { BaseOwnerSettingsSection } from "@/Components/Base/OwnerSettings";
import type { BaseOwner } from "@/Components/Base/OwnerSettings";
import {
  useSettingsOwnerActions,
  useSettingsOwners,
  useUserSettings,
} from "@/Components/Settings/Hooks";
import styles from "@/Styles/modules/SettingsPage.module.css";

export const SettingsPage: React.FC = () => {
  const { t } = useTranslation();

  const { data, isLoading, isError, updateMutation } = useUserSettings();
  const { data: owners, isLoading: isLoadingOwners, isError: isErrorOwners } = useSettingsOwners();
  const actions = useSettingsOwnerActions();

  const mappedOwners: BaseOwner[] = useMemo(() => {
    if (!owners) return [];
    return owners.map((owner) => {
      const statusLower = (owner.status || "incomplete").toLowerCase();
      const isErr = statusLower === "error";
      const isTokErr = statusLower === "token_error";
      return {
        id: owner.owner_id,
        name: owner.name,
        owner_type: owner.owner_type,
        avatar_url: owner.icon,
        subtitle: owner.ticker ? `[${owner.ticker}]` : undefined,
        status: owner.status,
        has_error: isErr || isTokErr,
        error_message: owner.error_message,
        last_sync: owner.last_sync,
        sections: owner.sections?.map((sec) => ({
          section: sec.section,
          section_name: sec.section_name,
          is_success: sec.is_success,
          has_token_error: sec.has_token_error,
          error_message: sec.error_message,
          last_run_finished_at: sec.last_update_finished_at,
        })),
      };
    });
  }, [owners]);

  if (isLoading) {
    return (
      <div className="aa-loader-container">
        <span className="spinner-border" />
        <span>{t("Loading settings…")}</span>
      </div>
    );
  }

  if (isError || !data) {
    return (
      <Card className="bg-secondary text-light border-0 shadow-sm" role="alert">
        <Card.Body className={styles["error"]}>
          {t("Failed to load settings. Please try refreshing the page.")}
        </Card.Body>
      </Card>
    );
  }

  return (
    <Card className={`${styles["page"]} border-0`}>
      <Card.Body className="bg-dark">
        <Card.Header className={styles["header"] + " bg-secondary"}>
          <Settings2 size={24} aria-hidden="true" />
          <div>
            <h1 className={styles["title"]}>{t("Settings")}</h1>
            <p className={styles["description"]}>{t("Manage your TaxSystem preferences.")}</p>
          </div>
        </Card.Header>

        <Card className="bg-secondary text-light border-0 shadow-sm mb-4">
          <Card.Body className={styles["setting-row"]}>
            <div className={styles["setting-copy"]}>
              <div className={styles["setting-title"]}>
                <BellOff size={18} aria-hidden="true" />
                <label htmlFor="disable-notifications">{t("Disable all notifications")}</label>
              </div>
              <p className={styles["setting-description"]}>
                {t("When enabled, TaxSystem will not send notifications to your Alliance Auth or Discord account.")}
              </p>
              {updateMutation.isError && (
                <p className={styles["error-message"]} role="alert">
                  {t("Could not save this setting. Your previous preference was restored.")}
                </p>
              )}
              {updateMutation.isPending && (
                <p className={styles["save-status"]} role="status">{t("Saving…")}</p>
              )}
            </div>
            <input
              id="disable-notifications"
              className={styles["switch"]}
              type="checkbox"
              role="switch"
              checked={data.disable_notifications}
              disabled={updateMutation.isPending}
              onChange={(event) =>
                updateMutation.mutate({ disable_notifications: event.currentTarget.checked })
              }
            />
          </Card.Body>
        </Card>

        {/* Modular BaseOwnerSettingsSection for Owners */}
        <BaseOwnerSettingsSection<BaseOwner>
          title={t("Owners Update Status")}
          description={t("ESI synchronization status of your linked corporations and alliances.")}
          icon={<Users size={20} aria-hidden="true" />}
          owners={mappedOwners}
          isLoading={isLoadingOwners}
          isError={isErrorOwners}
          errorMessage={t("Failed to load owners update status.")}
          emptyMessage={t("No TaxSystem owners configured.")}
          appName="TaxSystem"
          onUpdateAll={actions.updateAll}
          isUpdatingAll={actions.isUpdatingAll}
          globalCooldown={actions.globalCooldown}
          feedbackMessage={actions.feedback}
          onDismissFeedback={actions.clearFeedback}
          onTriggerSingleUpdate={actions.updateOwner}
          updatingOwnerId={actions.updatingOwnerId}
          ownerCooldowns={actions.ownerCooldowns}
          onDeleteOwner={(owner) => actions.deleteOwner(owner.id)}
          isDeleting={actions.isDeleting}
          deleteModalTitle={t("Delete Owner")}
          deleteModalDescription={(owner) =>
            t(
              "Are you sure you want to remove {{name}} from TaxSystem? All payment configurations, member records, and tax accounts for this owner will be permanently deleted.",
              { name: owner.name },
            )
          }
        />
      </Card.Body>
    </Card>
  );
};

export default SettingsPage;
