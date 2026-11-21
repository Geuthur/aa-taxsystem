// Third Party
import { apiErrorMessage } from "aa-geuthur-react";

// AA TaxSystem
import { apiClient } from "@/Api/Api";
import type { components } from "@/Api/OpenApi";
import { ProjectName } from "@/constants";

/** Query keys of the tax accounts of an owner area. */
export const taxAccountsQueryKeys = {
  accounts: (ownerId: number) => ["TaxAccounts", ownerId] as const,
};

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
    throw new Error(apiErrorMessage(error, "Failed to load tax accounts"));
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
    throw new Error(apiErrorMessage(error, "Failed to switch tax account"));
  }
  return data as { success: boolean; message: string };
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
    throw new Error(apiErrorMessage(error, "Failed to add custom payment"));
  }
  return data as { success?: boolean; message?: string };
}
