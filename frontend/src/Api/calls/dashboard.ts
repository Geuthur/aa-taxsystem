// Third Party
import { apiErrorMessage } from "aa-geuthur-react";

// AA TaxSystem
import { apiClient } from "@/Api/Api";
import type { components } from "@/Api/OpenApi";
import { ProjectName } from "@/constants";

/** Query keys of the owner dashboard and owner settings area. */
export const dashboardQueryKeys = {
  dashboard: (ownerId: number) => ["Dashboard", ownerId] as const,
};

export async function loadDashboard(ownerId: number): Promise<components["schemas"]["DashboardResponse"]> {
  const { data, error } = await apiClient.GET(
    `/${ProjectName}/api/corporation/{owner_id}/view/dashboard/`,
    {
      params: { path: { owner_id: ownerId } },
    },
  );
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to load dashboard"));
  }
  return data;
}

export async function updateOwnerSettings(
  ownerId: number,
  settings: components["schemas"]["UpdateOwnerSettingsRequest"],
): Promise<{ success: boolean; message: string }> {
  const { data, error } = await apiClient.POST(
    `/${ProjectName}/api/owner/{owner_id}/manage/settings/`,
    {
      params: { path: { owner_id: ownerId } },
      body: settings,
    },
  );
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to update owner settings"));
  }
  return data as { success: boolean; message: string };
}
