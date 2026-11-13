// Third Party
import { FilterButtonGroup } from "aa-geuthur-react";
import { Building2, Shield, Users } from "lucide-react";

export interface OwnerTypeFilterProps {
  ownerType: string;
  setOwnerType: (ownerType: string) => void;
  t: (key: string) => string;
}

export function OwnerTypeFilter({
  ownerType,
  setOwnerType,
  t,
}: OwnerTypeFilterProps) {
  const options = [
    { value: "all", label: t("All"), icon: <Users size={13} /> },
    { value: "corporation", label: t("Corporations"), icon: <Building2 size={13} /> },
    { value: "alliance", label: t("Alliances"), icon: <Shield size={13} /> },
  ];

  return (
    <FilterButtonGroup
      value={ownerType}
      onChange={setOwnerType}
      options={options}
      ariaLabel="Filter owners by type"
    />
  );
}

export default OwnerTypeFilter;

