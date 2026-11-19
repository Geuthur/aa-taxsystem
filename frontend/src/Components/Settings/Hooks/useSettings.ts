// React
import { useState } from "react";

// Third Party
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useCooldown, useFeedback, useOwnerCooldowns } from "aa-geuthur-react";
import { useTranslation } from "react-i18next";

// AA TaxSystem
import {
  deleteOwner,
  loadSettingsOwners,
  triggerOwnerUpdate,
  triggerUpdateAllTaxOwners,
} from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";

/** Loads the owners the user may manage. */
export function useSettingsOwners() {
  return useQuery({
    queryKey: queryKeys.SettingsOwners,
    queryFn: loadSettingsOwners,
  });
}

/**
 * Update-all, single update and delete for the owners on the settings page,
 * including feedback messages and cooldowns.
 */
export function useSettingsOwnerActions() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const { seconds: globalCooldown, start: startGlobalCooldown } = useCooldown();
  const { cooldowns: ownerCooldowns, start: startOwnerCooldown } = useOwnerCooldowns();
  const { feedback, showFeedback, clearFeedback } = useFeedback();
  const [updatingOwnerId, setUpdatingOwnerId] = useState<number | null>(null);

  const invalidateQueries = () => {
    queryClient.invalidateQueries({ queryKey: queryKeys.SettingsOwners });
    queryClient.invalidateQueries({ queryKey: queryKeys.Overview });
    queryClient.invalidateQueries({ queryKey: queryKeys.AdministrationOwners });
  };

  const updateAllMutation = useMutation({
    mutationFn: () => triggerUpdateAllTaxOwners(false),
    onSuccess: (res) => {
      showFeedback("success", res.message || t("Update all task queued."));
      startGlobalCooldown(60);
      invalidateQueries();
    },
    onError: (err: unknown) => {
      showFeedback(
        "danger",
        err instanceof Error ? err.message : t("Failed to queue update all task."),
      );
    },
  });

  const updateOwnerMutation = useMutation({
    mutationFn: (ownerId: number) => triggerOwnerUpdate({ ownerId, forceRefresh: false }),
    onSuccess: (res, ownerId) => {
      showFeedback("success", res.message || t("Owner update task queued."));
      startOwnerCooldown(ownerId, 60);
      invalidateQueries();
    },
    onError: (err: unknown) => {
      showFeedback(
        "danger",
        err instanceof Error ? err.message : t("Failed to trigger owner update."),
      );
    },
    onSettled: () => {
      setUpdatingOwnerId(null);
    },
  });

  const deleteOwnerMutation = useMutation({
    mutationFn: (ownerId: number) => deleteOwner(ownerId),
    onSuccess: (res) => {
      showFeedback("success", res.message || t("Owner removed successfully."));
      invalidateQueries();
    },
    onError: (err: unknown) => {
      showFeedback("danger", err instanceof Error ? err.message : t("Failed to delete owner."));
    },
  });

  const updateOwner = (ownerId: number) => {
    setUpdatingOwnerId(ownerId);
    updateOwnerMutation.mutate(ownerId);
  };

  return {
    feedback,
    clearFeedback,
    globalCooldown,
    ownerCooldowns,
    updatingOwnerId,
    updateAll: () => updateAllMutation.mutate(),
    isUpdatingAll: updateAllMutation.isPending,
    updateOwner,
    deleteOwner: (ownerId: number) => deleteOwnerMutation.mutateAsync(ownerId),
    isDeleting: deleteOwnerMutation.isPending,
  };
}
