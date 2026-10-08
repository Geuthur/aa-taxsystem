// React
import { useMemo } from "react";
import { Link } from "react-router-dom";

// Third Party
import { useQuery } from "@tanstack/react-query";
import {
  Building2,
  CreditCard,
  FileText,
  Search,
  Settings,
  Shield,
  UserCheck,
} from "lucide-react";
import { Badge, Card, Col, Form, InputGroup, Row, Spinner } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// AA TaxSystem
import { loadOverview } from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";
import BaseSectionHeader from "@/Components/Base/BaseHeader";
import { OwnerTypeFilter } from "@/Components/Overview/OwnerTypeFilter";
import { useStatusFilterState, useTableSearchState } from "@/Hooks/useTaxsystemState";

export function OverviewPage() {
  const { t } = useTranslation();
  const [search, setSearch] = useTableSearchState("search");
  const [ownerType, setOwnerType] = useStatusFilterState("type");

  const { data, isLoading, isError, error } = useQuery({
    queryKey: queryKeys.Overview,
    queryFn: loadOverview,
  });

  const filteredOwners = useMemo(() => {
    if (!data?.owners) return [];
    return data.owners.filter((owner) => {
      const matchesSearch =
        !search || owner.name.toLowerCase().includes(search.toLowerCase());
      const matchesType =
        ownerType === "all" || owner.type === ownerType;
      return matchesSearch && matchesType;
    });
  }, [data, search, ownerType]);

  return (
    <main>
      <BaseSectionHeader name={t("Tax System Overview")}>
        <div className="d-flex align-items-center gap-2">
          <Badge bg="secondary" className="px-3 py-2">
            {filteredOwners.length} {t("Owners")}
          </Badge>
        </div>
      </BaseSectionHeader>

      <div className="mt-3 p-3 aa-panel rounded">
        <Row className="g-3 align-items-center mb-4">
          <Col md={6} lg={4}>
            <InputGroup>
              <InputGroup.Text className="bg-dark border-secondary text-secondary">
                <Search size={16} />
              </InputGroup.Text>
              <Form.Control
                type="text"
                placeholder={t("Search corporations & alliances...")}
                value={search}
                onChange={(e) => setSearch(e.target.value)}
                className="bg-dark text-light border-secondary"
              />
            </InputGroup>
          </Col>
          <OwnerTypeFilter
            ownerType={ownerType}
            setOwnerType={setOwnerType}
            t={t}
          />
        </Row>

        {isLoading && (
          <div className="text-center py-5">
            <Spinner animation="border" variant="primary" />
            <div className="mt-2 text-muted">{t("Loading tax system owners...")}</div>
          </div>
        )}

        {isError && (
          <div className="alert alert-danger" role="alert">
            {error instanceof Error ? error.message : t("Failed to load overview")}
          </div>
        )}

        {!isLoading && !isError && filteredOwners.length === 0 && (
          <div className="text-center py-5 text-muted">
            <Shield size={48} className="mb-3 opacity-50" />
            <h5>{t("No tax system owners found")}</h5>
            <p className="small">
              {t("No owners match your search query.")}
            </p>
          </div>
        )}

        <Row className="g-3">
          {filteredOwners.map((owner) => (
            <Col key={`${owner.type}-${owner.id}`} xs={12} md={6} lg={4}>
              <Card className="h-100 aa-card border-secondary shadow-sm">
                <Card.Body className="d-flex flex-column justify-content-between p-3">
                  <div>
                    <div className="d-flex align-items-center gap-3 mb-3">
                      {owner.portrait_url ? (
                        <img
                          src={owner.portrait_url}
                          alt={owner.name}
                          width={48}
                          height={48}
                          className="rounded-circle border border-secondary"
                        />
                      ) : (
                        <div
                          className="rounded-circle bg-secondary d-flex align-items-center justify-content-center"
                          style={{ width: 48, height: 48 }}
                        >
                          {owner.type === "corporation" ? <Building2 size={24} /> : <Shield size={24} />}
                        </div>
                      )}
                      <div className="overflow-hidden">
                        <h5 className="mb-0 text-truncate text-light">{owner.name}</h5>
                        <div className="d-flex align-items-center gap-2 mt-1">
                          <Badge bg={owner.type === "corporation" ? "info" : "warning"} className="text-dark">
                            {owner.type_display}
                          </Badge>
                          <Badge bg={owner.active ? "success" : "secondary"}>
                            {owner.active ? t("Active") : t("Inactive")}
                          </Badge>
                        </div>
                      </div>
                    </div>

                    <div className="d-flex align-items-center justify-content-between mb-3 p-2 rounded bg-dark border border-secondary small">
                      <span className="text-muted">{t("Open Invoices")}</span>
                      <Badge bg={owner.open_invoices > 0 ? "danger" : "secondary"} pill>
                        {owner.open_invoices}
                      </Badge>
                    </div>
                  </div>

                  <div className="d-flex flex-wrap gap-2 pt-2 border-top border-secondary">
                    <Link
                      to={`account/${owner.id}/`}
                      className="aa-btn aa-btn-sm aa-btn-success flex-fill d-flex align-items-center justify-content-center gap-1"
                    >
                      <UserCheck size={14} />
                      {t("Account")}
                    </Link>
                    <Link
                      to={`payments/${owner.id}/`}
                      className="aa-btn aa-btn-sm aa-btn-secondary flex-fill d-flex align-items-center justify-content-center gap-1"
                    >
                      <CreditCard size={14} />
                      {t("Payments")}
                    </Link>
                    <Link
                      to={`my-payments/${owner.id}/`}
                      className="aa-btn aa-btn-sm aa-btn-secondary flex-fill d-flex align-items-center justify-content-center gap-1"
                    >
                      <FileText size={14} />
                      {t("My Payments")}
                    </Link>
                    {owner.can_manage && (
                      <Link
                        to={`owner/${owner.id}/`}
                        className="aa-btn aa-btn-sm aa-btn-warning flex-fill d-flex align-items-center justify-content-center gap-1"
                      >
                        <Settings size={14} />
                        {t("Manage")}
                      </Link>
                    )}
                  </div>
                </Card.Body>
              </Card>
            </Col>
          ))}
        </Row>
      </div>
    </main>
  );
}

export default OverviewPage;
