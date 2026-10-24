// React
import React, { useEffect, useMemo, useState } from "react";

// Third Party
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { BellOff, Settings2, Users } from "lucide-react";
import { Card } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// AA TaxSystem
import {
  deleteOwner,
  loadSettingsOwners,
  loadUserSettings,
  triggerOwnerUpdate,
  triggerUpdateAllTaxOwners,
  updateUserSettings,
} from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";
import type { UserSettingsSchema } from "@/Api/schema";
import { BaseOwnerSettingsSection } from "@/Components/Base/OwnerSettings";
import type { BaseOwner } from "@/Components/Base/OwnerSettings";
import styles from "@/Styles/modules/SettingsPage.module.css";

export const SettingsPage: React.FC = () => {
  const { t } = useTranslation();
  const queryClient = useQueryClient();

  // Cooldown & Feedback States
  const [globalCooldown, setGlobalCooldown] = useState(0);
  const [updatingOwnerId, setUpdatingOwnerId] = useState<number | null>(null);
  const [ownerCooldowns, setOwnerCooldowns] = useState<Record<number, number>>({});
  const [feedbackMsg, setFeedbackMsg] = useState<{ variant: "success" | "danger"; text: string } | null>(null);

  useEffect(() => {
    if (globalCooldown <= 0) return;
    const timer = setInterval(() => {
      setGlobalCooldown((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(timer);
  }, [globalCooldown]);

  useEffect(() => {
    const activeCooldowns = Object.values(ownerCooldowns).some((v) => v > 0);
    if (!activeCooldowns) return;
    const timer = setInterval(() => {
      setOwnerCooldowns((prev) => {
        const next: Record<number, number> = {};
        for (const [key, val] of Object.entries(prev)) {
          if (val > 1) next[Number(key)] = val - 1;
        }
        return next;
      });
    }, 1000);
    return () => clearInterval(timer);
  }, [ownerCooldowns]);

  const { data, isLoading, isError } = useQuery({
    queryKey: queryKeys.UserSettings,
    queryFn: loadUserSettings,
  });

  const {
    data: owners,
    isLoading: isLoadingOwners,
    isError: isErrorOwners,
  } = useQuery({
    queryKey: queryKeys.SettingsOwners,
    queryFn: loadSettingsOwners,
  });

  const invalidateQueries = () => {
    queryClient.invalidateQueries({ queryKey: queryKeys.SettingsOwners });
    queryClient.invalidateQueries({ queryKey: queryKeys.Overview });
    queryClient.invalidateQueries({ queryKey: queryKeys.AdministrationOwners });
  };

  const updateMutation = useMutation({
    mutationFn: updateUserSettings,
    onMutate: async (settings) => {
      await queryClient.cancelQueries({ queryKey: queryKeys.UserSettings });
      const previous = queryClient.getQueryData<UserSettingsSchema>(queryKeys.UserSettings);
      queryClient.setQueryData<UserSettingsSchema>(queryKeys.UserSettings, settings);
      return { previous };
    },
    onError: (_error, _settings, context) => {
      if (context?.previous) {
        queryClient.setQueryData(queryKeys.UserSettings, context.previous);
      }
    },
    onSuccess: (settings) => {
      queryClient.setQueryData(queryKeys.UserSettings, settings);
    },
  });

  const updateAllMutation = useMutation({
    mutationFn: () => triggerUpdateAllTaxOwners(false),
    onSuccess: (res) => {
      setFeedbackMsg({ variant: "success", text: res.message || t("Update all task queued.") });
      setGlobalCooldown(60);
      invalidateQueries();
      setTimeout(() => setFeedbackMsg(null), 5000);
    },
    onError: (err: unknown) => {
      setFeedbackMsg({
        variant: "danger",
        text: err instanceof Error ? err.message : t("Failed to queue update all task."),
      });
      setTimeout(() => setFeedbackMsg(null), 5000);
    },
  });

  const updateOwnerMutation = useMutation({
    mutationFn: (ownerId: number) => triggerOwnerUpdate({ ownerId, forceRefresh: false }),
    onSuccess: (res, ownerId) => {
      setFeedbackMsg({ variant: "success", text: res.message || t("Owner update task queued.") });
      setOwnerCooldowns((prev) => ({ ...prev, [ownerId]: 60 }));
      invalidateQueries();
      setTimeout(() => setFeedbackMsg(null), 5000);
    },
    onError: (err: unknown) => {
      setFeedbackMsg({
        variant: "danger",
        text: err instanceof Error ? err.message : t("Failed to trigger owner update."),
      });
      setTimeout(() => setFeedbackMsg(null), 5000);
    },
    onSettled: () => {
      setUpdatingOwnerId(null);
    },
  });

  const handleTriggerOwnerUpdate = (ownerId: number) => {
    setUpdatingOwnerId(ownerId);
    updateOwnerMutation.mutate(ownerId);
  };

  const deleteOwnerMutation = useMutation({
    mutationFn: (ownerId: number) => deleteOwner(ownerId),
    onSuccess: (res) => {
      setFeedbackMsg({ variant: "success", text: res.message || t("Owner removed successfully.") });
      invalidateQueries();
      setTimeout(() => setFeedbackMsg(null), 5000);
    },
    onError: (err: unknown) => {
      setFeedbackMsg({
        variant: "danger",
        text: err instanceof Error ? err.message : t("Failed to delete owner."),
      });
      setTimeout(() => setFeedbackMsg(null), 5000);
    },
  });

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
        <span>{t("Loading settings...")}</span>
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
                <p className={styles["save-status"]} role="status">{t("Saving...")}</p>
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
          onUpdateAll={() => updateAllMutation.mutate()}
          isUpdatingAll={updateAllMutation.isPending}
          globalCooldown={globalCooldown}
          feedbackMessage={feedbackMsg}
          onDismissFeedback={() => setFeedbackMsg(null)}
          onTriggerSingleUpdate={handleTriggerOwnerUpdate}
          updatingOwnerId={updatingOwnerId}
          ownerCooldowns={ownerCooldowns}
          onDeleteOwner={(owner) => deleteOwnerMutation.mutateAsync(owner.id)}
          isDeleting={deleteOwnerMutation.isPending}
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
