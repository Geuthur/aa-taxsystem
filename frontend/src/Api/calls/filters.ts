// Third Party
import { apiErrorMessage } from "aa-geuthur-react";

// AA TaxSystem
import { apiClient } from "@/Api/Api";
import type { components } from "@/Api/OpenApi";
import { ProjectName } from "@/constants";

/** Query keys of the filter sets and filters area. */
export const filtersQueryKeys = {
  filterSets: (ownerId: number) => ["FilterSets", ownerId] as const,
  filters: (ownerId: number, filterSetPk?: number) => ["Filters", ownerId, filterSetPk] as const,
};

export async function loadFilterSets(
  ownerId: number,
): Promise<components["schemas"]["FilterSetModelSchema"][]> {
  const { data, error } = await apiClient.GET(
    `/${ProjectName}/api/owner/{owner_id}/view/filter-set/`,
    {
      params: { path: { owner_id: ownerId } },
    },
  );
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to load filter sets"));
  }
  return data as unknown as components["schemas"]["FilterSetModelSchema"][];
}

export async function loadFilters(
  ownerId: number,
  filterSetPk: number,
): Promise<components["schemas"]["FilterModelSchema"][]> {
  const { data, error } = await apiClient.GET(
    `/${ProjectName}/api/owner/{owner_id}/filter-set/{filterset_pk}/view/filter/`,
    {
      params: { path: { owner_id: ownerId, filterset_pk: filterSetPk } },
    },
  );
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to load filters"));
  }
  return data as unknown as components["schemas"]["FilterModelSchema"][];
}

export async function createFilterSet(
  ownerId: number,
  payload: components["schemas"]["CreateFilterSetRequest"],
): Promise<components["schemas"]["MessageSchema"]> {
  const { data, error } = await apiClient.POST(
    `/${ProjectName}/api/owner/{owner_id}/filter-set/create/`,
    {
      params: { path: { owner_id: ownerId } },
      body: payload,
    },
  );
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to create filter set"));
  }
  return data;
}

export async function createFilter(
  ownerId: number,
  payload: components["schemas"]["CreateFilterRequest"],
): Promise<components["schemas"]["MessageSchema"]> {
  const { data, error } = await apiClient.POST(
    `/${ProjectName}/api/owner/{owner_id}/filter/create/`,
    {
      params: { path: { owner_id: ownerId } },
      body: payload,
    },
  );
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to create filter"));
  }
  return data;
}

export async function deleteFilter(
  ownerId: number,
  filterPk: number,
  comment: string = "Deleted via TaxSystem",
): Promise<{ success?: boolean; message?: string }> {
  const { data, error } = await apiClient.POST(
    `/${ProjectName}/api/owner/{owner_id}/filter/{filter_pk}/manage/delete-filter/`,
    {
      params: { path: { owner_id: ownerId, filter_pk: filterPk } },
      body: { comment },
    },
  );
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to delete filter"));
  }
  return data as { success?: boolean; message?: string };
}

export async function deleteFilterSet(
  ownerId: number,
  filtersetPk: number,
  comment: string = "Deleted via TaxSystem",
): Promise<{ success?: boolean; message?: string }> {
  const { data, error } = await apiClient.POST(
    `/${ProjectName}/api/owner/{owner_id}/filter-set/{filterset_pk}/manage/delete-filter/`,
    {
      params: { path: { owner_id: ownerId, filterset_pk: filtersetPk } },
      body: { comment },
    },
  );
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to delete filter set"));
  }
  return data as { success?: boolean; message?: string };
}

export async function switchFilterSet(
  ownerId: number,
  filtersetPk: number,
): Promise<{ success?: boolean; message?: string }> {
  const { data, error } = await apiClient.POST(
    `/${ProjectName}/api/owner/{owner_id}/filter-set/{filterset_pk}/manage/switch-filter/`,
    {
      params: { path: { owner_id: ownerId, filterset_pk: filtersetPk } },
    },
  );
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to switch filter set"));
  }
  return data as { success?: boolean; message?: string };
}
