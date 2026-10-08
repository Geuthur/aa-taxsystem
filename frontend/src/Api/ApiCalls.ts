// AA TaxSystem
import { ProjectName } from "../../configuration";
import { apiClient } from "@/Api/Api";
import type { components } from "@/Api/OpenApi";

export async function loadUserData(): Promise<{ user: components["schemas"]["UserData"] }> {
  const { data, error } = await apiClient.GET(`/${ProjectName}/api/user/`);
  if (error || !data) {
    throw new Error("Failed to load user data");
  }
  return { user: data };
}

export async function loadUserSettings(): Promise<components["schemas"]["UserSettingsSchema"]> {
  const { data, error } = await apiClient.GET(`/${ProjectName}/api/settings/`);
  if (error || !data) {
    throw new Error("Failed to load user settings");
  }
  return data;
}

export async function loadMenu(): Promise<components["schemas"]["MenuSchema"]> {
  const { data, error } = await apiClient.GET(`/${ProjectName}/api/menu/`);
  if (error || !data) {
    throw new Error("Failed to load menu");
  }
  return data;
}

export async function updateUserSettings(
  settings: components["schemas"]["UserSettingsUpdateRequest"],
): Promise<components["schemas"]["UserSettingsSchema"]> {
  const { data, error } = await apiClient.PUT(`/${ProjectName}/api/settings/`, {
    body: settings,
  });

  if (error || !data) {
    throw new Error("Failed to update user settings");
  }
  return data;
}

export async function loadOverview(): Promise<components["schemas"]["OverviewSchema"]> {
  const { data, error } = await apiClient.GET(`/${ProjectName}/api/overview/`);
  if (error || !data) {
    throw new Error("Failed to load overview");
  }
  return data;
}

export async function loadDashboard(ownerId: number): Promise<components["schemas"]["DashboardResponse"]> {
  const { data, error } = await apiClient.GET(
    `/${ProjectName}/api/corporation/{owner_id}/view/dashboard/`,
    {
      params: { path: { owner_id: ownerId } },
    },
  );
  if (error || !data) {
    throw new Error("Failed to load dashboard");
  }
  return data;
}

export async function loadTaxAccounts(
  ownerId: number,
): Promise<components["schemas"]["PaymentSystemSchema"][]> {
  const { data, error } = await apiClient.GET(
    `/${ProjectName}/api/owner/{owner_id}/manage/tax-accounts/`,
    {
      params: { path: { owner_id: ownerId } },
    },
  );
  if (error || !data) {
    throw new Error("Failed to load tax accounts");
  }
  return data as unknown as components["schemas"]["PaymentSystemSchema"][];
}

export async function switchTaxAccount(
  ownerId: number,
  accountPk: number,
): Promise<{ success: boolean; message: string }> {
  const { data, error } = await apiClient.POST(
    `/${ProjectName}/api/owner/{owner_id}/account/{account_pk}/manage/switch-account/`,
    {
      params: { path: { owner_id: ownerId, account_pk: accountPk } },
    },
  );
  if (error || !data) {
    throw new Error("Failed to switch tax account");
  }
  return data as { success: boolean; message: string };
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
    throw new Error("Failed to update owner settings");
  }
  return data as { success: boolean; message: string };
}

export async function updateTaxAmount(
  ownerId: number,
  taxAmount: number,
): Promise<{ success: boolean; message: string }> {
  const { data, error } = await apiClient.POST(
    `/${ProjectName}/api/owner/{owner_id}/manage/update-tax/`,
    {
      params: { path: { owner_id: ownerId } },
      body: { tax_amount: taxAmount },
    },
  );
  if (error || !data) {
    throw new Error("Failed to update tax amount");
  }
  return data as { success: boolean; message: string };
}

export async function updateTaxPeriod(
  ownerId: number,
  taxPeriod: number,
): Promise<{ success: boolean; message: string }> {
  const { data, error } = await apiClient.POST(
    `/${ProjectName}/api/owner/{owner_id}/manage/update-period/`,
    {
      params: { path: { owner_id: ownerId } },
      body: { tax_period: taxPeriod },
    },
  );
  if (error || !data) {
    throw new Error("Failed to update tax period");
  }
  return data as { success: boolean; message: string };
}

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
    throw new Error("Failed to load members");
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
    throw new Error("Failed to delete member");
  }
  return data as { success?: boolean; message?: string };
}

export async function loadPayments(
  ownerId: number,
  options?: { scope?: "all" | "mine"; characterId?: number },
): Promise<components["schemas"]["PaymentCorporationSchema"][]> {
  const queryParams: Record<string, string | number> = {};
  if (options?.scope) {
    queryParams.scope = options.scope;
  }
  if (options?.characterId !== undefined) {
    queryParams.character_id = options.characterId;
  }
  const { data, error } = await apiClient.GET(
    `/${ProjectName}/api/owner/{owner_id}/payments/`,
    {
      params: {
        path: { owner_id: ownerId },
        query: queryParams as never,
      },
    },
  );
  if (error || !data) {
    throw new Error("Failed to load payments");
  }
  return data as unknown as components["schemas"]["PaymentCorporationSchema"][];
}

export async function loadMyPayments(
  ownerId: number,
): Promise<components["schemas"]["PaymentSchema"][]> {
  const { data, error } = await apiClient.GET(
    `/${ProjectName}/api/owner/{owner_id}/view/my-payments/`,
    {
      params: { path: { owner_id: ownerId } },
    },
  );
  if (error || !data) {
    throw new Error("Failed to load personal payments");
  }
  return data as unknown as components["schemas"]["PaymentSchema"][];
}

export async function loadPaymentDetails(
  ownerId: number,
  paymentPk: number,
): Promise<components["schemas"]["PaymentsDetailsResponse"]> {
  const { data, error } = await apiClient.GET(
    `/${ProjectName}/api/owner/{owner_id}/payment/{payment_pk}/view/details/`,
    {
      params: { path: { owner_id: ownerId, payment_pk: paymentPk } },
    },
  );
  if (error || !data) {
    throw new Error("Failed to load payment details");
  }
  return data;
}

export async function managePaymentAction(
  ownerId: number,
  paymentPk: number,
  action: "approve" | "reject" | "undo" | "delete",
  comment?: string,
): Promise<{ success: boolean; message: string }> {
  const { data, error } = await apiClient.POST(
    `/${ProjectName}/api/owner/{owner_id}/payment/{payment_pk}/manage/action/`,
    {
      params: { path: { owner_id: ownerId, payment_pk: paymentPk } },
      body: { action, comment: comment ?? "" },
    },
  );
  if (error || !data) {
    throw new Error(`Failed to ${action} payment`);
  }
  return data as { success: boolean; message: string };
}

export async function manageBulkPaymentAction(
  ownerId: number,
  paymentIds: number[],
  action: "approve" | "reject" | "undo" | "delete",
  comment?: string,
): Promise<components["schemas"]["BulkPaymentActionResponse"]> {
  const { data, error } = await apiClient.POST(
    `/${ProjectName}/api/owner/{owner_id}/manage/payments/bulk-action/`,
    {
      params: { path: { owner_id: ownerId } },
      body: { payment_ids: paymentIds, action, comment: comment ?? "" },
    },
  );
  if (error || !data) {
    throw new Error(`Failed to bulk ${action} payments`);
  }
  return data;
}

export async function approvePayment(
  ownerId: number,
  paymentPk: number,
  comment?: string,
): Promise<{ success: boolean; message: string }> {
  const { data, error } = await apiClient.POST(
    `/${ProjectName}/api/owner/{owner_id}/payment/{payment_pk}/manage/approve-payment/`,
    {
      params: { path: { owner_id: ownerId, payment_pk: paymentPk } },
      body: { comment: comment ?? "" },
    },
  );
  if (error || !data) {
    throw new Error("Failed to approve payment");
  }
  return data as { success: boolean; message: string };
}

export const acceptPayment = approvePayment;

export async function rejectPayment(
  ownerId: number,
  paymentPk: number,
  comment?: string,
): Promise<{ success: boolean; message: string }> {
  const { data, error } = await apiClient.POST(
    `/${ProjectName}/api/owner/{owner_id}/payment/{payment_pk}/manage/reject-payment/`,
    {
      params: { path: { owner_id: ownerId, payment_pk: paymentPk } },
      body: { comment: comment ?? "" },
    },
  );
  if (error || !data) {
    throw new Error("Failed to reject payment");
  }
  return data as { success: boolean; message: string };
}

export async function undoPayment(
  ownerId: number,
  paymentPk: number,
  comment?: string,
): Promise<{ success: boolean; message: string }> {
  const { data, error } = await apiClient.POST(
    `/${ProjectName}/api/owner/{owner_id}/payment/{payment_pk}/manage/undo-payment/`,
    {
      params: { path: { owner_id: ownerId, payment_pk: paymentPk } },
      body: { comment: comment ?? "" },
    },
  );
  if (error || !data) {
    throw new Error("Failed to undo payment");
  }
  return data as { success: boolean; message: string };
}

export async function deletePayment(
  ownerId: number,
  paymentPk: number,
  comment: string = "Deleted via TaxSystem",
): Promise<{ success?: boolean; message?: string }> {
  const { data, error } = await apiClient.POST(
    `/${ProjectName}/api/owner/{owner_id}/payment/{payment_pk}/manage/delete-payment/`,
    {
      params: { path: { owner_id: ownerId, payment_pk: paymentPk } },
      body: { comment },
    },
  );
  if (error || !data) {
    throw new Error("Failed to delete payment");
  }
  return data as { success?: boolean; message?: string };
}

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
    throw new Error("Failed to load filter sets");
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
    throw new Error("Failed to load filters");
  }
  return data as unknown as components["schemas"]["FilterModelSchema"][];
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
    throw new Error("Failed to delete filter");
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
    throw new Error("Failed to delete filter set");
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
    throw new Error("Failed to switch filter set");
  }
  return data as { success?: boolean; message?: string };
}

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
    throw new Error("Failed to load groups");
  }
  return data as unknown as components["schemas"]["GroupManagementSchema"][];
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
    throw new Error("Failed to delete group");
  }
  return data as { success?: boolean; message?: string };
}

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
    throw new Error("Failed to load admin logs");
  }
  return data as unknown as components["schemas"]["AdminHistorySchema"][];
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
    throw new Error("Failed to run admin tasks");
  }
  return data;
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
    throw new Error("Failed to load member payments");
  }
  return data;
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
    const msg = (error as { error?: string })?.error || "Failed to create filter set";
    throw new Error(msg);
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
    const msg = (error as { error?: string })?.error || "Failed to create filter";
    throw new Error(msg);
  }
  return data;
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
    throw new Error("Failed to load available groups");
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
    const msg = (error as { error?: string })?.error || "Failed to create group";
    throw new Error(msg);
  }
  return data;
}

export async function loadUserAccounts(): Promise<components["schemas"]["UserAccountSchema"][]> {
  const { data, error } = await apiClient.GET(
    `/${ProjectName}/api/user/accounts/`,
  );
  if (error || !data) {
    throw new Error("Failed to load user tax accounts");
  }
  return data;
}

export async function addCustomPayment(
  ownerId: number,
  accountPk: number,
  payload: components["schemas"]["AddPaymentRequest"],
): Promise<{ success?: boolean; message?: string }> {
  const { data, error } = await apiClient.POST(
    `/${ProjectName}/api/owner/{owner_id}/account/{account_pk}/manage/add-payment/`,
    {
      params: { path: { owner_id: ownerId, account_pk: accountPk } },
      body: payload,
    },
  );
  if (error || !data) {
    throw new Error("Failed to add custom payment");
  }
  return data as { success?: boolean; message?: string };
}
