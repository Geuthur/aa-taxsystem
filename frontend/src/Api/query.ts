// Third Party
import { queryKeys as baseQueryKeys } from "aa-geuthur-react";

// Every key that influences a request is part of the key, so URL state changes refetch.
// `Menu`, `User` and `UserSettings` come from the package, so its hooks and the app share them.
export const queryKeys = {
  ...baseQueryKeys,
  Overview: ["Overview"] as const,
  Dashboard: (ownerId: number) => ["Dashboard", ownerId] as const,
  TaxAccounts: (ownerId: number) => ["TaxAccounts", ownerId] as const,
  Members: (ownerId: number) => ["Members", ownerId] as const,
  Payments: (ownerId: number) => ["Payments", ownerId] as const,
  MyPayments: (ownerId: number) => ["MyPayments", ownerId] as const,
  PaymentDetails: (ownerId: number, paymentPk: number) =>
    ["PaymentDetails", ownerId, paymentPk] as const,
  FilterSets: (ownerId: number) => ["FilterSets", ownerId] as const,
  Filters: (ownerId: number, filterSetPk?: number) => ["Filters", ownerId, filterSetPk] as const,
  Groups: (ownerId: number) => ["Groups", ownerId] as const,
  AvailableGroups: (ownerId: number) => ["AvailableGroups", ownerId] as const,
  MemberPayments: (ownerId: number, characterId: number) =>
    ["MemberPayments", ownerId, characterId] as const,
  AdminLogs: (ownerId: number) => ["AdminLogs", ownerId] as const,
  UserAccounts: ["UserAccounts"] as const,
  AdministrationOwners: ["AdministrationOwners"] as const,
  AdministrationOwnerInspect: (ownerType: string, ownerId: number) =>
    ["AdministrationOwnerInspect", ownerType, ownerId] as const,
  SettingsOwners: ["SettingsOwners"] as const,
};

