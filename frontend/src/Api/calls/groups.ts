// Third Party
import { apiErrorMessage } from "aa-geuthur-react";

// AA TaxSystem
import { apiClient } from "@/Api/Api";
import type { components } from "@/Api/OpenApi";
import { ProjectName } from "@/constants";

/** Query keys of the tax groups area. */
export const groupsQueryKeys = {
  groups: (ownerId: number) => ["Groups", ownerId] as const,
  available: (ownerId: number) => ["AvailableGroups", ownerId] as const,
};

export async function loadGroups(
  ownerId: number,
): Promise<components["schemas"]["GroupManagementSchema"][]> {
  const { data, error } = await apiClient.GET(
    `/${ProjectName}/api/owner/{owner_id}/groups/`,
    {
      params: { path: { owner_id: ownerId } },
    },
  );
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to load groups"));
  }
  return data as unknown as components["schemas"]["GroupManagementSchema"][];
}

export async function loadAvailableGroups(
  ownerId: number,
): Promise<components["schemas"]["GroupSchema"][]> {
  const { data, error } = await apiClient.GET(
    `/${ProjectName}/api/owner/{owner_id}/groups/available/`,
    {
      params: { path: { owner_id: ownerId } },
    },
  );
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to load available groups"));
  }
  return data;
}

export async function createGroup(
  ownerId: number,
  payload: components["schemas"]["CreateGroupRequest"],
): Promise<components["schemas"]["MessageSchema"]> {
  const { data, error } = await apiClient.POST(
    `/${ProjectName}/api/owner/{owner_id}/groups/create/`,
    {
      params: { path: { owner_id: ownerId } },
      body: payload,
    },
  );
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to create group"));
  }
  return data;
}

export async function deleteGroup(
  ownerId: number,
  groupPk: number,
  comment: string = "Deleted via Tax System",
): Promise<{ success?: boolean; message?: string }> {
  const { data, error } = await apiClient.POST(
    `/${ProjectName}/api/owner/{owner_id}/groups/{group_pk}/manage/delete/`,
    {
      params: { path: { owner_id: ownerId, group_pk: groupPk } },
      body: { comment },
    },
  );
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to delete group"));
  }
  return data as { success?: boolean; message?: string };
}
