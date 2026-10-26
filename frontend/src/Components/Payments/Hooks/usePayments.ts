// Third Party
import { useQuery } from "@tanstack/react-query";

// AA TaxSystem
// AA Tax System
import { loadMyPayments, loadPaymentDetails, loadPayments } from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";

/** Loads all payments of an owner (disabled until an owner is set). */
export function usePayments(ownerId: number) {
  return useQuery({
    queryKey: queryKeys.Payments(ownerId),
    queryFn: () => loadPayments(ownerId),
    enabled: ownerId > 0,
  });
}

/** Loads the details of one payment; stays disabled until a payment is selected. */
export function usePaymentDetails(ownerId: number, paymentId: number | null) {
  return useQuery({
    queryKey: queryKeys.PaymentDetails(ownerId, paymentId || 0),
    queryFn: () => loadPaymentDetails(ownerId, paymentId!),
    enabled: Boolean(paymentId && paymentId > 0),
  });
}

/** Loads the payments of the current user for an owner (disabled until an owner is set). */
export function useMyPayments(ownerId: number) {
  return useQuery({
    queryKey: queryKeys.MyPayments(ownerId),
    queryFn: () => loadMyPayments(ownerId),
    enabled: ownerId > 0,
  });
}
