// Third Party
import { apiErrorMessage } from "aa-geuthur-react";

// AA TaxSystem
import { apiClient } from "@/Api/Api";
import type { components } from "@/Api/OpenApi";
import { ProjectName } from "@/constants";

/** Query keys of the payments area. */
export const paymentsQueryKeys = {
  payments: (ownerId: number) => ["Payments", ownerId] as const,
  myPayments: (ownerId: number) => ["MyPayments", ownerId] as const,
  details: (ownerId: number, paymentPk: number) =>
    ["PaymentDetails", ownerId, paymentPk] as const,
};

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
    throw new Error(apiErrorMessage(error, "Failed to load payments"));
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
    throw new Error(apiErrorMessage(error, "Failed to load personal payments"));
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
    throw new Error(apiErrorMessage(error, "Failed to load payment details"));
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
    throw new Error(apiErrorMessage(error, `Failed to ${action} payment`));
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
    throw new Error(apiErrorMessage(error, `Failed to bulk ${action} payments`));
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
    throw new Error(apiErrorMessage(error, "Failed to approve payment"));
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
    throw new Error(apiErrorMessage(error, "Failed to reject payment"));
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
    throw new Error(apiErrorMessage(error, "Failed to undo payment"));
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
    throw new Error(apiErrorMessage(error, "Failed to delete payment"));
  }
  return data as { success?: boolean; message?: string };
}
