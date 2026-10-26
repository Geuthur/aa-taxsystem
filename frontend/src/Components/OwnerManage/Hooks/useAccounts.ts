// Third Party
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

// AA TaxSystem
// AA Tax System
import { addCustomPayment, loadTaxAccounts, switchTaxAccount } from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";

/** Loads the tax accounts of an owner. */
export function useTaxAccounts(ownerId: number) {
  return useQuery({
    queryKey: queryKeys.TaxAccounts(ownerId),
    queryFn: () => loadTaxAccounts(ownerId),
  });
}

/**
 * Switch the state of a tax account and add custom payments.
 * @param callbacks `onSwitched` and `onPaymentAdded` reset the dialog state of the caller
 */
export function useAccountActions(
  ownerId: number,
  callbacks: { onSwitched?: () => void; onPaymentAdded?: () => void } = {},
) {
  const queryClient = useQueryClient();

  const switchMutation = useMutation({
    mutationFn: ({ accountPk }: { accountPk: number }) => switchTaxAccount(ownerId, accountPk),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.TaxAccounts(ownerId) });
      callbacks.onSwitched?.();
    },
  });

  const addPaymentMutation = useMutation({
    mutationFn: ({
      accountPk,
      amount,
      comment,
    }: {
      accountPk: number;
      amount: number;
      comment: string;
    }) => addCustomPayment(ownerId, accountPk, { amount, comment: comment.trim() }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.TaxAccounts(ownerId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.Payments(ownerId) });
      callbacks.onPaymentAdded?.();
    },
  });

  return {
    switchAccount: switchMutation.mutate,
    isSwitching: switchMutation.isPending,
    addPayment: addPaymentMutation.mutate,
    isAddingPayment: addPaymentMutation.isPending,
  };
}
