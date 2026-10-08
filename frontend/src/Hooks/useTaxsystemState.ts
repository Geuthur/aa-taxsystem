// Third Party
import { parseAsString, parseAsStringLiteral, useQueryState } from "nuqs";

export const OWNER_TABS = [
  "accounts",
  "members",
  "filters",
  "groups",
  "history",
] as const;

export type OwnerTab = (typeof OWNER_TABS)[number];

export function useOwnerTabState() {
  const [tab, setTab] = useQueryState(
    "tab",
    parseAsStringLiteral(OWNER_TABS).withDefault("accounts"),
  );

  return [tab, setTab] as const;
}

export function useTableSearchState(key = "search") {
  const [search, setSearch] = useQueryState(
    key,
    parseAsString.withDefault(""),
  );

  return [search, setSearch] as const;
}

export function useStatusFilterState(key = "status") {
  const [status, setStatus] = useQueryState(
    key,
    parseAsString.withDefault("all"),
  );

  return [status, setStatus] as const;
}
