// Third Party
import { apiErrorMessage } from "aa-geuthur-react";

// AA TaxSystem
import { apiClient } from "@/Api/Api";
import type { components } from "@/Api/OpenApi";
import { ProjectName } from "@/constants";

/** Query keys of the overview area. */
export const overviewQueryKeys = {
  overview: ["Overview"] as const,
};

export async function loadOverview(): Promise<components["schemas"]["OverviewSchema"]> {
  const { data, error } = await apiClient.GET(`/${ProjectName}/api/overview/`);
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to load overview"));
  }
  return data;
}
