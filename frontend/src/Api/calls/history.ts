// Third Party
import { apiErrorMessage } from "aa-geuthur-react";

// AA TaxSystem
import { apiClient } from "@/Api/Api";
import type { components } from "@/Api/OpenApi";
import { ProjectName } from "@/constants";

/** Query keys of the admin history of an owner area. */
export const historyQueryKeys = {
  adminLogs: (ownerId: number) => ["AdminLogs", ownerId] as const,
};

export async function loadAdminLogs(
  ownerId: number,
): Promise<components["schemas"]["AdminHistorySchema"][]> {
  const { data, error } = await apiClient.GET(
    `/${ProjectName}/api/owner/{owner_id}/view/admin-history/`,
    {
      params: { path: { owner_id: ownerId } },
    },
  );
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to load admin logs"));
  }
  return data as unknown as components["schemas"]["AdminHistorySchema"][];
}
