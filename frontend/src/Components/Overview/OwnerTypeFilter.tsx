// Third Party
import { Building2, Shield, Users } from "lucide-react";
import { Button } from "react-bootstrap";

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
  return (
    <div className="btn-group" role="group">
      <Button
        className={`aa-btn aa-btn-sm ${ownerType === "all" ? "aa-btn-primary" : "aa-btn-secondary"}`}
        onClick={() => setOwnerType("all")}
      >
        <Users size={13} className="me-1" />
        {t("All")}
      </Button>
      <Button
        className={`aa-btn aa-btn-sm ${ownerType === "corporation" ? "aa-btn-primary" : "aa-btn-secondary"}`}
        onClick={() => setOwnerType("corporation")}
      >
        <Building2 size={13} className="me-1" />
        {t("Corporations")}
      </Button>
      <Button
        className={`aa-btn aa-btn-sm ${ownerType === "alliance" ? "aa-btn-primary" : "aa-btn-secondary"}`}
        onClick={() => setOwnerType("alliance")}
      >
        <Shield size={13} className="me-1" />
        {t("Alliances")}
      </Button>
    </div>
  );
}

export default OwnerTypeFilter;
