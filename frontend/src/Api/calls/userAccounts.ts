// Third Party
import { apiErrorMessage } from "aa-geuthur-react";

// AA TaxSystem
import { apiClient } from "@/Api/Api";
import type { components } from "@/Api/OpenApi";
import { ProjectName } from "@/constants";

/** Query keys of the tax accounts of the user area. */
export const userAccountsQueryKeys = {
  accounts: ["UserAccounts"] as const,
};

export async function loadUserAccounts(): Promise<components["schemas"]["UserAccountSchema"][]> {
  const { data, error } = await apiClient.GET(
    `/${ProjectName}/api/user/accounts/`,
  );
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to load user tax accounts"));
  }
  return data;
}
