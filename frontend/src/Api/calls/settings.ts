// Third Party
import { apiErrorMessage } from "aa-geuthur-react";

// AA TaxSystem
import { apiClient } from "@/Api/Api";
import type { components } from "@/Api/OpenApi";
import { ProjectName } from "@/constants";

/** Query keys of the settings area. */
export const settingsQueryKeys = {
  owners: ["SettingsOwners"] as const,
};

export async function loadSettingsOwners(): Promise<components["schemas"]["TaxOwnerSettingSchema"][]> {
  const { data, error } = await apiClient.GET(
    `/${ProjectName}/api/settings/owners/`,
  );
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to load settings owners"));
  }
  return data;
}

export async function triggerUpdateAllTaxOwners(
  forceRefresh?: boolean,
): Promise<components["schemas"]["MessageSchema"]> {
  const { data, error } = await apiClient.POST(
    `/${ProjectName}/api/settings/owners/update-all/`,
    {
      body: { force_refresh: forceRefresh ?? false },
    },
  );
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to trigger update all owners"));
  }
  return data;
}

export async function triggerOwnerUpdate(params: {
  ownerId: number;
  forceRefresh?: boolean;
}): Promise<components["schemas"]["MessageSchema"]> {
  const { data, error } = await apiClient.POST(
    `/${ProjectName}/api/owner/{owner_id}/update/`,
    {
      params: { path: { owner_id: params.ownerId } },
      body: { force_refresh: params.forceRefresh ?? false },
    },
  );
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to trigger update"));
  }
  return data;
}

export async function deleteOwner(ownerId: number): Promise<components["schemas"]["MessageSchema"]> {
  const { data, error } = await apiClient.DELETE(
    `/${ProjectName}/api/owner/{owner_id}/`,
    {
      params: { path: { owner_id: ownerId } },
    },
  );
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to delete owner"));
  }
  return data;
}
