// Third Party
import { useQuery } from "@tanstack/react-query";

// AA TaxSystem
// AA Tax System
import { loadUserAccounts, userAccountsQueryKeys } from "@/Api/calls/userAccounts";

/** Loads the tax accounts of the current user. */
export function useUserAccounts() {
  return useQuery({
    queryKey: userAccountsQueryKeys.accounts,
    queryFn: loadUserAccounts,
  });
}
