// Third Party
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

// AA TaxSystem
// AA Tax System
import { historyQueryKeys, loadAdminLogs } from "@/Api/calls/history";
import { deleteMember, loadMemberPayments, loadMembers, membersQueryKeys } from "@/Api/calls/members";

/** Loads the members of an owner. */
export function useMembers(ownerId: number) {
  return useQuery({
    queryKey: membersQueryKeys.members(ownerId),
    queryFn: () => loadMembers(ownerId),
  });
}

/** Loads the payments of one member; only runs while the member dialog is open. */
export function useMemberPayments(ownerId: number, characterId: number | null, enabled: boolean) {
  return useQuery({
    queryKey: characterId ? membersQueryKeys.payments(ownerId, characterId) : ["MemberPayments", ownerId],
    queryFn: () => (characterId ? loadMemberPayments(ownerId, characterId) : Promise.resolve([])),
    enabled: enabled && characterId !== null,
  });
}

/**
 * Remove a member of an owner.
 * @param onDeleted Resets the dialog state of the caller
 */
export function useMemberActions(ownerId: number, onDeleted?: () => void) {
  const queryClient = useQueryClient();
  const deleteMutation = useMutation({
    mutationFn: (memberPk: number) => deleteMember(ownerId, memberPk),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: membersQueryKeys.members(ownerId) });
      onDeleted?.();
    },
  });

  return { remove: deleteMutation.mutate, isRemoving: deleteMutation.isPending };
}

/** Loads the admin history of an owner. */
export function useAdminLogs(ownerId: number) {
  return useQuery({
    queryKey: historyQueryKeys.adminLogs(ownerId),
    queryFn: () => loadAdminLogs(ownerId),
  });
}
