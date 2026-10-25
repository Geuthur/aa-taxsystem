// Third Party
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

// AA TaxSystem
// AA Tax System
import { createGroup, deleteGroup, loadAvailableGroups, loadGroups } from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";

/** Loads the tax groups of an owner. */
export function useGroups(ownerId: number) {
  return useQuery({
    queryKey: queryKeys.Groups(ownerId),
    queryFn: () => loadGroups(ownerId),
  });
}

/** Loads the Alliance Auth groups that can be assigned; only runs while the create dialog is open. */
export function useAvailableGroups(ownerId: number, enabled: boolean) {
  return useQuery({
    queryKey: queryKeys.AvailableGroups(ownerId),
    queryFn: () => loadAvailableGroups(ownerId),
    enabled,
  });
}

/**
 * Create and delete tax groups of an owner.
 * @param callbacks `onCreated` and `onDeleted` reset the dialog state of the caller
 */
export function useGroupActions(
  ownerId: number,
  callbacks: { onCreated?: () => void; onDeleted?: () => void } = {},
) {
  const queryClient = useQueryClient();
  const refresh = () => queryClient.invalidateQueries({ queryKey: queryKeys.Groups(ownerId) });

  const createMutation = useMutation({
    mutationFn: ({ name, groupIds }: { name: string; groupIds: number[] }) =>
      createGroup(ownerId, { name: name.trim(), group_ids: groupIds }),
    onSuccess: () => {
      refresh();
      callbacks.onCreated?.();
    },
  });

  const deleteMutation = useMutation({
    mutationFn: ({ groupPk, comment }: { groupPk: number; comment: string }) =>
      deleteGroup(ownerId, groupPk, comment),
    onSuccess: () => {
      refresh();
      callbacks.onDeleted?.();
    },
  });

  return {
    create: createMutation.mutate,
    isCreating: createMutation.isPending,
    remove: deleteMutation.mutate,
    isRemoving: deleteMutation.isPending,
  };
}
