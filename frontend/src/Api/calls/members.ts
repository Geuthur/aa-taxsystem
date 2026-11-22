// Third Party
import { apiErrorMessage } from "aa-geuthur-react";

// AA TaxSystem
import { apiClient } from "@/Api/Api";
import type { components } from "@/Api/OpenApi";
import { ProjectName } from "@/constants";

/** Query keys of the members of an owner area. */
export const membersQueryKeys = {
  members: (ownerId: number) => ["Members", ownerId] as const,
  payments: (ownerId: number, characterId: number) =>
    ["MemberPayments", ownerId, characterId] as const,
};

export async function loadMembers(
  ownerId: number,
): Promise<components["schemas"]["MembersSchema"][]> {
  const { data, error } = await apiClient.GET(
    `/${ProjectName}/api/owner/{owner_id}/view/members/`,
    {
      params: { path: { owner_id: ownerId } },
    },
  );
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to load members"));
  }
  return data as unknown as components["schemas"]["MembersSchema"][];
}

export async function deleteMember(
  ownerId: number,
  memberPk: number,
  comment?: string,
): Promise<{ success?: boolean; message?: string }> {
  const { data, error } = await apiClient.POST(
    `/${ProjectName}/api/owner/{owner_id}/member/{member_pk}/manage/delete-member/`,
    {
      params: { path: { owner_id: ownerId, member_pk: memberPk } },
      body: { comment: comment ?? "" },
    },
  );
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to delete member"));
  }
  return data as { success?: boolean; message?: string };
}

export async function loadMemberPayments(
  ownerId: number,
  characterId: number,
): Promise<components["schemas"]["PaymentSchema"][]> {
  const { data, error } = await apiClient.GET(
    `/${ProjectName}/api/owner/{owner_id}/character/{character_id}/view/payments/`,
    {
      params: { path: { owner_id: ownerId, character_id: characterId } },
    },
  );
  if (error || !data) {
    throw new Error(apiErrorMessage(error, "Failed to load member payments"));
  }
  return data;
}
