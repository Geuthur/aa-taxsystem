// Third Party
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

// AA TaxSystem
// AA Tax System
import { loadDashboard, updateOwnerSettings } from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";

/** Loads the dashboard of an owner (disabled until an owner is set). */
export function useDashboard(ownerId: number) {
  return useQuery({
    queryKey: queryKeys.Dashboard(ownerId),
    queryFn: () => loadDashboard(ownerId),
    enabled: ownerId > 0,
  });
}

/** Saves the tax amount and period of an owner and refreshes its dashboard. */
export function useUpdateOwnerSettings(ownerId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (settings: { tax_amount?: number; tax_period?: number }) =>
      updateOwnerSettings(ownerId, settings),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.Dashboard(ownerId) });
    },
  });
}
