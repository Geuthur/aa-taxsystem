// Third Party
import { useQuery } from "@tanstack/react-query";

// AA TaxSystem
// AA Tax System
import { loadOverview } from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";

/** Loads all owners shown on the overview page. */
export function useOverview() {
  return useQuery({
    queryKey: queryKeys.Overview,
    queryFn: loadOverview,
  });
}
