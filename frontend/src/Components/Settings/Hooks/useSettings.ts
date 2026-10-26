// React
import { useState } from "react";

// Third Party
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useTranslation } from "react-i18next";

// AA TaxSystem
// AA Tax System
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
import { useCooldown, useOwnerCooldowns } from "@/Hooks/useCooldown";
import { useFeedback } from "@/Hooks/useFeedback";

/** Loads the user settings and updates them optimistically. */
export function useUserSettings() {
  const queryClient = useQueryClient();

  const query = useQuery({
    queryKey: queryKeys.UserSettings,
    queryFn: loadUserSettings,
  });

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

  return { ...query, updateMutation };
}

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
