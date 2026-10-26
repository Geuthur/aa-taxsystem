// Third Party
import { useQuery } from "@tanstack/react-query";

// AA TaxSystem
// AA Tax System
import { loadMenu, loadSettingsOwners } from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";

/** Loads the left and right menu links. */
export function useMenu() {
  return useQuery({
    queryKey: queryKeys.Menu,
    queryFn: () => loadMenu(),
    staleTime: 5 * 60 * 1000,
    retry: 1,
    refetchOnWindowFocus: false,
  });
}

/** Loads the owners of the user, refreshed every 30 seconds, to show sync issues in the menu. */
export function useMenuOwnerStatus() {
  return useQuery({
    queryKey: queryKeys.SettingsOwners,
    queryFn: () => loadSettingsOwners(),
    refetchInterval: 30000,
    staleTime: 15000,
  });
}
