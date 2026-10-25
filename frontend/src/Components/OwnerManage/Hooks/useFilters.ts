// Third Party
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

// AA TaxSystem
// AA Tax System
import {
  createFilter,
  createFilterSet,
  deleteFilter,
  deleteFilterSet,
  loadFilterSets,
  loadFilters,
} from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";

/** Loads the filter sets of an owner. */
export function useFilterSets(ownerId: number) {
  return useQuery({
    queryKey: queryKeys.FilterSets(ownerId),
    queryFn: () => loadFilterSets(ownerId),
  });
}

/** Loads the filters of a filter set; stays disabled until a set is selected. */
export function useFilters(ownerId: number, filterSetId: number | null) {
  return useQuery({
    queryKey: queryKeys.Filters(ownerId, filterSetId ?? undefined),
    queryFn: () => (filterSetId ? loadFilters(ownerId, filterSetId) : Promise.resolve([])),
    enabled: filterSetId !== null,
  });
}

/**
 * Create and delete filter sets and filters of an owner.
 * @param activeSetId The selected filter set (its filters are refreshed after a delete)
 * @param callbacks Reset the dialog state of the caller after each action
 */
export function useFilterActions(
  ownerId: number,
  activeSetId: number | null,
  callbacks: {
    onSetCreated?: () => void;
    onFilterCreated?: () => void;
    onSetDeleted?: () => void;
    onFilterDeleted?: () => void;
  } = {},
) {
  const queryClient = useQueryClient();

  const createSetMutation = useMutation({
    mutationFn: ({ name, description }: { name: string; description: string }) =>
      createFilterSet(ownerId, { name: name.trim(), description: description.trim() }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.FilterSets(ownerId) });
      callbacks.onSetCreated?.();
    },
  });

  const createFilterMutation = useMutation({
    mutationFn: ({
      filterSetId,
      filterType,
      matchType,
      value,
    }: {
      filterSetId: number | null;
      filterType: "reason" | "amount";
      matchType: "exact" | "contains";
      value: string;
    }) => {
      if (!filterSetId) throw new Error("No filter set selected");
      return createFilter(ownerId, {
        filter_set_id: filterSetId,
        filter_type: filterType,
        match_type: matchType,
        value: value.trim(),
      });
    },
    onSuccess: (_data, variables) => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.Filters(ownerId, variables.filterSetId ?? undefined),
      });
      callbacks.onFilterCreated?.();
    },
  });

  const deleteSetMutation = useMutation({
    mutationFn: (filtersetPk: number) => deleteFilterSet(ownerId, filtersetPk),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.FilterSets(ownerId) });
      callbacks.onSetDeleted?.();
    },
  });

  const deleteFilterMutation = useMutation({
    mutationFn: (filterPk: number) => deleteFilter(ownerId, filterPk),
    onSuccess: () => {
      queryClient.invalidateQueries({
        queryKey: queryKeys.Filters(ownerId, activeSetId ?? undefined),
      });
      callbacks.onFilterDeleted?.();
    },
  });

  return {
    createSet: createSetMutation.mutate,
    isCreatingSet: createSetMutation.isPending,
    createFilter: createFilterMutation.mutate,
    isCreatingFilter: createFilterMutation.isPending,
    removeSet: deleteSetMutation.mutate,
    isRemovingSet: deleteSetMutation.isPending,
    removeFilter: deleteFilterMutation.mutate,
    isRemovingFilter: deleteFilterMutation.isPending,
  };
}
