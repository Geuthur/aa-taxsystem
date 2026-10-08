export const queryKeys = {
  Menu: ["Menu"] as const,
  User: ["User"] as const,
  UserSettings: ["UserSettings"] as const,
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
};
