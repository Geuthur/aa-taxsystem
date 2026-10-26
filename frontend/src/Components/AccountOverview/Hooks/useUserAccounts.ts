// Third Party
import { useQuery } from "@tanstack/react-query";

// AA TaxSystem
// AA Tax System
import { loadUserAccounts } from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";

/** Loads the tax accounts of the current user. */
export function useUserAccounts() {
  return useQuery({
    queryKey: queryKeys.UserAccounts,
    queryFn: loadUserAccounts,
  });
}
