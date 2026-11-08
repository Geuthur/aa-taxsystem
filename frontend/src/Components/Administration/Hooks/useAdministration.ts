// React
import { useState } from "react";

// Third Party
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useUserData } from "aa-geuthur-react";

// AA TaxSystem
// AA Tax System
import {
  deleteAdministrationOwner,
  loadAdministrationOwners,
  runAdminTasks,
  triggerAdministrationOwnerUpdate,
} from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";

/** Loads all owners of the Administration. */
export function useAdministrationOwners() {
  return useQuery({
    queryKey: queryKeys.AdministrationOwners,
    queryFn: loadAdministrationOwners,
  });
}

/** Tells whether the current user is an admin (`is_admin` of the user endpoint, the superuser flag: global tasks, force refresh). */
export function useIsAdmin() {
  const { data } = useUserData();
  return data?.user.is_admin ?? false;
}

/**
 * Global tasks, single owner update and delete for the Administration,
 * including the success and error message.
 * @param onDeleted Called after an owner was deleted successfully
 */
export function useAdministrationActions(onDeleted?: () => void) {
  const queryClient = useQueryClient();
  const [message, setMessage] = useState<string | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  const showSuccess = (text: string) => {
    setMessage(text);
    setErrorMessage(null);
  };
  const showError = (text: string) => {
    setErrorMessage(text);
    setMessage(null);
  };
  const refreshOwners = () =>
    queryClient.invalidateQueries({ queryKey: queryKeys.AdministrationOwners });

  const globalTaskMutation = useMutation({
    mutationFn: (vars: Parameters<typeof runAdminTasks>[0]) => runAdminTasks(vars),
    onSuccess: (data) => showSuccess(data.message),
    onError: (err: Error) => showError(err.message),
  });

  const updateMutation = useMutation({
    mutationFn: (vars: Parameters<typeof triggerAdministrationOwnerUpdate>[0]) =>
      triggerAdministrationOwnerUpdate(vars),
    onSuccess: (data) => {
      showSuccess(data.message);
      refreshOwners();
    },
    onError: (err: Error) => showError(err.message),
  });

  const deleteMutation = useMutation({
    mutationFn: (vars: Parameters<typeof deleteAdministrationOwner>[0]) =>
      deleteAdministrationOwner(vars),
    onSuccess: (data) => {
      showSuccess(data.message);
      onDeleted?.();
      refreshOwners();
    },
    onError: (err: Error) => showError(err.message),
  });

  return {
    message,
    errorMessage,
    clearMessage: () => setMessage(null),
    clearErrorMessage: () => setErrorMessage(null),
    runTasks: globalTaskMutation.mutate,
    isRunningTasks: globalTaskMutation.isPending,
    updateOwner: updateMutation.mutate,
    isUpdating: updateMutation.isPending,
    deleteOwner: deleteMutation.mutate,
    isDeleting: deleteMutation.isPending,
  };
}
