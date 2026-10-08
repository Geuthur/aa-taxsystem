// Third Party
import { Building2, Shield, Users } from "lucide-react";
import { Button, Col } from "react-bootstrap";

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
    <Col md={6} lg={8} className="d-flex justify-content-md-end gap-2">
      <Button
        size="sm"
        onClick={() => setOwnerType("all")}
        className={ownerType === "all" ? "aa-btn aa-btn-primary" : "aa-btn aa-btn-secondary"}
      >
        <Users size={14} className="me-1" />
        {t("All")}
      </Button>
      <Button
        size="sm"
        onClick={() => setOwnerType("corporation")}
        className={ownerType === "corporation" ? "aa-btn aa-btn-primary" : "aa-btn aa-btn-secondary"}
      >
        <Building2 size={14} className="me-1" />
        {t("Corporations")}
      </Button>
      <Button
        size="sm"
        onClick={() => setOwnerType("alliance")}
        className={ownerType === "alliance" ? "aa-btn aa-btn-primary" : "aa-btn aa-btn-secondary"}
      >
        <Shield size={14} className="me-1" />
        {t("Alliances")}
      </Button>
    </Col>
  );
}
