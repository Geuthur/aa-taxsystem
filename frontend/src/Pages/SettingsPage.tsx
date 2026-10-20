// React
import React, { useEffect, useState } from "react";

// Third Party
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertCircle,
  AlertTriangle,
  BellOff,
  Building2,
  CheckCircle2,
  Clock,
  RotateCw,
  Settings2,
  Trash2,
  Users,
} from "lucide-react";
import { Alert, Button, Card, Spinner } from "react-bootstrap";
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
import type { TaxOwnerSettingSchema, UserSettingsSchema } from "@/Api/schema";
import { BaseModal, ModalSize } from "@/Components/Base/BaseModal";
import styles from "@/Styles/modules/SettingsPage.module.css";

export const SettingsPage: React.FC = () => {
  const { t } = useTranslation();
  const queryClient = useQueryClient();

  // Cooldown & Modal States
  const [globalCooldown, setGlobalCooldown] = useState(0);
  const [updatingOwnerId, setUpdatingOwnerId] = useState<number | null>(null);
  const [ownerCooldowns, setOwnerCooldowns] = useState<Record<number, number>>({});
  const [ownerToDelete, setOwnerToDelete] = useState<TaxOwnerSettingSchema | null>(null);
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
    queryClient.invalidateQueries({ queryKey: queryKeys.SuperuserOwners });
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
      setOwnerToDelete(null);
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

  const handleConfirmDelete = async () => {
    if (ownerToDelete) {
      await deleteOwnerMutation.mutateAsync(ownerToDelete.owner_id);
    }
  };

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

  const renderStatusBadge = (owner: TaxOwnerSettingSchema) => {
    const status = owner.status.toLowerCase();
    const isError = status === "error";
    const isTokenError = status === "token_error";
    const isOk = status === "ok";
    const isDisabled = status === "disabled";

    let badgeClass = styles["badge-incomplete"];
    let label = t("Incomplete");
    let Icon = AlertTriangle;

    if (isOk) {
      badgeClass = styles["badge-ok"];
      label = t("OK");
      Icon = CheckCircle2;
    } else if (isError) {
      badgeClass = styles["badge-error"];
      label = t("Error");
      Icon = AlertCircle;
    } else if (isTokenError) {
      badgeClass = styles["badge-token-error"];
      label = t("Token Error");
      Icon = AlertTriangle;
    } else if (isDisabled) {
      badgeClass = styles["badge-disabled"];
      label = t("Disabled");
      Icon = AlertCircle;
    }

    return (
      <span className={`${styles["status-badge"]} ${badgeClass}`}>
        {(isError || isTokenError) && (
          <span className="aa-pending-dot-container me-1" aria-hidden="true">
            <span className={isError ? "aa-danger-dot-ping" : "aa-pending-dot-ping"} />
            <span className={isError ? "aa-danger-dot-core" : "aa-pending-dot-core"} />
          </span>
        )}
        <Icon size={12} aria-hidden="true" />
        <span>{label}</span>
      </span>
    );
  };

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

        {/* Added Owners Update Status & Management Section */}
        <Card className={`${styles["section"]} border-0 shadow-sm`} aria-labelledby="owner-status-heading">
          <Card.Body className="bg-secondary text-light">
            <Card.Header className={`${styles["section-header"]} bg-secondary d-flex justify-content-between align-items-center flex-wrap gap-2`}>
              <div className={styles["section-title-wrap"]}>
                <Users size={20} aria-hidden="true" />
                <h2 id="owner-status-heading" className={styles["section-title"]}>
                  {t("Owners Update Status")}
                </h2>
                {owners && (
                  <span className={styles["section-count"]}>
                    ({owners.length})
                  </span>
                )}
              </div>

              {owners && owners.length > 0 && (
                <Button
                  variant="secondary"
                  size="sm"
                  className="aa-btn aa-btn-secondary aa-btn-sm d-flex align-items-center gap-1"
                  disabled={updateAllMutation.isPending || globalCooldown > 0}
                  onClick={() => updateAllMutation.mutate()}
                >
                  {updateAllMutation.isPending ? (
                    <Spinner size="sm" animation="border" />
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

            {feedbackMsg && (
              <Alert
                variant={feedbackMsg.variant}
                className="py-2 my-3 d-flex justify-content-between align-items-center"
                dismissible
                onClose={() => setFeedbackMsg(null)}
              >
                <span>{feedbackMsg.text}</span>
              </Alert>
            )}

            {isLoadingOwners && (
              <div className="aa-loader-container">
                <span className="spinner-border" />
                <span>{t("Loading owners update status...")}</span>
              </div>
            )}

            {isErrorOwners && (
              <Card className="bg-secondary text-light border-0 shadow-sm" role="alert">
                <Card.Body className={styles["error"]}>
                  {t("Failed to load owners update status.")}
                </Card.Body>
              </Card>
            )}

            {!isLoadingOwners && !isErrorOwners && owners && owners.length === 0 && (
              <Card className="bg-secondary text-light border-0 shadow-sm">
                <Card.Body className={styles["empty-state"]}>
                  {t("No TaxSystem owners configured.")}
                </Card.Body>
              </Card>
            )}

            {!isLoadingOwners && !isErrorOwners && owners && owners.length > 0 && (
              <div className={styles["owners-grid"]}>
                {owners.map((owner) => {
                  const status = owner.status.toLowerCase();
                  const isErr = status === "error";
                  const isTokErr = status === "token_error";
                  const cardClass = isErr
                    ? styles["owner-card-error"]
                    : isTokErr
                      ? styles["owner-card-warning"]
                      : "";

                  const ownerCooldown = ownerCooldowns[owner.owner_id] ?? 0;
                  const isUpdating = updatingOwnerId === owner.owner_id;

                  return (
                    <Card
                      key={owner.owner_id}
                      className={`aa-panel ${styles["owner-card"]} ${cardClass}`}
                    >
                      <div className={styles["owner-header"]}>
                        {owner.icon ? (
                          <img
                            src={owner.icon}
                            alt={owner.name}
                            className={styles["portrait"]}
                          />
                        ) : (
                          <div className={`${styles["portrait"]} d-flex align-items-center justify-content-center bg-dark text-muted`}>
                            <Building2 size={24} />
                          </div>
                        )}
                        <div className={styles["owner-info"]}>
                          <h3 className={styles["owner-name"]}>{owner.name}</h3>
                          <p className={styles["owner-ticker"]}>
                            {owner.ticker ? `[${owner.ticker}] ` : ""}
                            <span className="text-capitalize">{owner.owner_type}</span>
                          </p>
                        </div>
                      </div>

                      {owner.error_message && (
                        <div className={styles["error-banner"]} role="alert">
                          {owner.error_message}
                        </div>
                      )}

                      {owner.sections && owner.sections.length > 0 && (
                        <div className={styles["sections-list"]}>
                          {owner.sections.map((sec) => {
                            let dotClass = styles["dot-muted"];
                            if (sec.is_success === true) dotClass = styles["dot-ok"];
                            else if (sec.is_success === false) dotClass = styles["dot-error"];
                            else if (sec.has_token_error) dotClass = styles["dot-warning"];

                            return (
                              <div key={sec.section} className={styles["section-item"]}>
                                <span className="d-inline-flex align-items-center gap-2">
                                  <span
                                    className={`${styles["section-dot"]} ${dotClass}`}
                                    aria-hidden="true"
                                  />
                                  <span>{sec.section_name}</span>
                                </span>
                                <span>
                                  {sec.has_token_error
                                    ? t("Token Error")
                                    : sec.is_success === true
                                      ? t("OK")
                                      : sec.is_success === false
                                        ? t("Failed")
                                        : t("Pending")}
                                </span>
                              </div>
                            );
                          })}
                        </div>
                      )}

                      <div className={styles["badge-row"]}>
                        {renderStatusBadge(owner)}
                        <span
                          className={styles["last-sync"]}
                          title={owner.last_sync ? `${t("Last sync")}: ${owner.last_sync}` : undefined}
                        >
                          <Clock size={12} aria-hidden="true" />
                          <span>{owner.last_sync ? owner.last_sync.slice(5) : t("Never")}</span>
                        </span>
                      </div>

                      {/* Owner Action Buttons: Update, Delete */}
                      <div className="d-flex align-items-center justify-content-end mt-3 pt-2 border-top border-secondary flex-wrap gap-2">
                        <Button
                          variant="secondary"
                          size="sm"
                          className="aa-btn aa-btn-secondary aa-btn-sm d-flex align-items-center gap-1"
                          disabled={isUpdating || ownerCooldown > 0}
                          onClick={() => handleTriggerOwnerUpdate(owner.owner_id)}
                          title={t("Update owner")}
                          aria-label={t("Update owner")}
                        >
                          {isUpdating ? (
                            <Spinner size="sm" animation="border" />
                          ) : (
                            <RotateCw size={13} />
                          )}
                          <span>
                            {ownerCooldown > 0 ? `${ownerCooldown}s` : t("Update")}
                          </span>
                        </Button>

                        <Button
                          variant="danger"
                          size="sm"
                          className="aa-btn aa-btn-danger aa-btn-sm d-flex align-items-center gap-1"
                          onClick={() => setOwnerToDelete(owner)}
                          title={t("Remove from TaxSystem")}
                          aria-label={t("Remove from TaxSystem")}
                        >
                          <Trash2 size={13} />
                          <span>{t("Delete")}</span>
                        </Button>
                      </div>
                    </Card>
                  );
                })}
              </div>
            )}
          </Card.Body>
        </Card>
      </Card.Body>

      {/* Delete Confirmation Modal */}
      <BaseModal
        show={Boolean(ownerToDelete)}
        onHide={() => setOwnerToDelete(null)}
        title={t("Delete Owner")}
        size={ModalSize.medium}
        footer={
          <>
            <Button
              variant="secondary"
              onClick={() => setOwnerToDelete(null)}
              className="aa-btn aa-btn-secondary"
            >
              {t("Cancel")}
            </Button>
            <Button
              variant="danger"
              onClick={handleConfirmDelete}
              disabled={deleteOwnerMutation.isPending}
              className="aa-btn aa-btn-danger d-flex align-items-center gap-1"
            >
              {deleteOwnerMutation.isPending ? (
                <Spinner size="sm" animation="border" />
              ) : (
                <Trash2 size={14} />
              )}
              <span>{t("Confirm Delete")}</span>
            </Button>
          </>
        }
      >
        <p className="text-light mb-0">
          {t("Are you sure you want to delete {{name}}? All associated data and configurations will be permanently removed.", {
            name: ownerToDelete?.name || "",
          })}
        </p>
      </BaseModal>
    </Card>
  );
};

export default SettingsPage;
