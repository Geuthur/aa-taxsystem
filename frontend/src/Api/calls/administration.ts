// Third Party
import { apiErrorMessage } from "aa-geuthur-react";

// AA TaxSystem
import { apiClient } from "@/Api/Api";
import type { components } from "@/Api/OpenApi";
import { ProjectName } from "@/constants";

/** Query keys of the administration area. */
export const administrationQueryKeys = {
  owners: ["AdministrationOwners"] as const,
  ownerInspect: (ownerType: string, ownerId: number) =>
    ["AdministrationOwnerInspect", ownerType, ownerId] as const,
};

export async function loadAdministrationOwners(): Promise<
  components["schemas"]["AdministrationTaxOwnerSchema"][]
> {
  const { data, error } = await apiClient.GET(
    `/${ProjectName}/api/administration/owners/`,
  );
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to load administration owners"));
  }
  return data;
}

export async function triggerAdministrationOwnerUpdate(params: {
  ownerType: "corporation" | "alliance";
  ownerId: number;
  payload?: components["schemas"]["AdministrationTaxOwnerUpdateRequest"];
}): Promise<components["schemas"]["MessageSchema"]> {
  const { data, error } = await apiClient.POST(
    `/${ProjectName}/api/administration/owners/{owner_type}/{owner_id}/update/`,
    {
      params: { path: { owner_type: params.ownerType, owner_id: params.ownerId } },
      body: params.payload ?? { force_refresh: false },
    },
  );
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to trigger update"));
  }
  return data;
}

export async function deleteAdministrationOwner(params: {
  ownerType: "corporation" | "alliance";
  ownerId: number;
}): Promise<components["schemas"]["MessageSchema"]> {
  const { data, error } = await apiClient.DELETE(
    `/${ProjectName}/api/administration/owners/{owner_type}/{owner_id}/`,
    {
      params: { path: { owner_type: params.ownerType, owner_id: params.ownerId } },
    },
  );
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to delete owner"));
  }
  return data;
}

export async function loadAdministrationOwnerInspect(params: {
  ownerType: "corporation" | "alliance";
  ownerId: number;
}): Promise<components["schemas"]["DashboardResponse"]> {
  const { data, error } = await apiClient.GET(
    `/${ProjectName}/api/administration/owners/{owner_type}/{owner_id}/inspect/`,
    {
      params: { path: { owner_type: params.ownerType, owner_id: params.ownerId } },
    },
  );
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to inspect owner dashboard"));
  }
  return data;
}

export async function runAdminTasks(
  payload: components["schemas"]["AdminUpdateRequest"],
): Promise<components["schemas"]["MessageSchema"]> {
  const { data, error } = await apiClient.POST(
    `/${ProjectName}/api/admin/tasks/run/`,
    {
      body: payload,
    },
  );
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to run admin tasks"));
  }
  return data;
}
