// Third Party
import { useQuery } from "@tanstack/react-query";

// AA TaxSystem
// AA Tax System
import { loadOverview, overviewQueryKeys } from "@/Api/calls/overview";

/** Loads all owners shown on the overview page. */
export function useOverview() {
  return useQuery({
    queryKey: overviewQueryKeys.overview,
    queryFn: loadOverview,
  });
}
