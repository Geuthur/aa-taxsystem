// React
import { useMemo } from "react";
import { Link, useParams } from "react-router-dom";

// Third Party
import { useQuery } from "@tanstack/react-query";
import {
  AlertCircle,
  ArrowRight,
  Calendar,
  CheckCircle,
  Clock,
  CreditCard,
  FileText,
  Search,
  User,
  Wallet,
} from "lucide-react";
import { Badge, Button, Col, Form, InputGroup, Row, Spinner } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// AA TaxSystem
import { loadUserAccounts } from "@/Api/ApiCalls";
import type { components } from "@/Api/OpenApi";
import { queryKeys } from "@/Api/query";
import BaseSectionHeader from "@/Components/Base/BaseHeader";
import { OwnerTypeFilter } from "@/Components/Overview/OwnerTypeFilter";
import { useStatusFilterState, useTableSearchState } from "@/Hooks/useTaxsystemState";
import {
  allianceImageUrl,
  characterImageUrl,
  corporationImageUrl,
  formatNumber,
  formatRelativeTime,
} from "@/Utils";

type UserAccount = components["schemas"]["UserAccountSchema"];

export function AccountOverviewPage() {
  const { t } = useTranslation();
  const { ownerId } = useParams<{ ownerId?: string }>();
  const filterOwnerId = ownerId ? Number(ownerId) : undefined;

  const [search, setSearch] = useTableSearchState("accountSearch");
  const [ownerType, setOwnerType] = useStatusFilterState("accountType");

  const {
    data: accounts,
    isLoading,
    isError,
    error,
    refetch,
  } = useQuery({
    queryKey: queryKeys.UserAccounts,
    queryFn: loadUserAccounts,
  });

  const filteredAccounts = useMemo<UserAccount[]>(() => {
    if (!accounts) return [];
    return accounts.filter((acc) => {
      if (filterOwnerId && acc.owner_id !== filterOwnerId) {
        return false;
      }
      const matchesSearch =
        !search ||
        acc.name.toLowerCase().includes(search.toLowerCase()) ||
        acc.owner_name.toLowerCase().includes(search.toLowerCase()) ||
        (acc.character_name &&
          acc.character_name.toLowerCase().includes(search.toLowerCase()));

      const matchesType = ownerType === "all" || acc.owner_type === ownerType;

      return matchesSearch && matchesType;
    });
  }, [accounts, filterOwnerId, search, ownerType]);

  return (
    <main className="d-flex flex-column gap-3">
      <BaseSectionHeader name={t("Member Account Overview")}>
        <div className="d-flex align-items-center gap-2">
          {filterOwnerId && (
            <Link
              to="/account/"
              className="aa-btn aa-btn-sm aa-btn-secondary"
            >
              <ArrowRight size={14} />
              {t("Show All Owners")}
            </Link>
          )}
        </div>
      </BaseSectionHeader>

      <div className="p-3 aa-panel rounded">
        <Row className="g-3 align-items-center mb-4">
          <Col md={6} lg={4}>
            <InputGroup>
              <InputGroup.Text className="bg-dark border-secondary text-secondary">
                <Search size={16} />
              </InputGroup.Text>
              <Form.Control
                type="text"
                placeholder={t("Filter accounts by character or owner...")}
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
            <div className="mt-2 text-muted">
              {t("Loading account details...")}
            </div>
          </div>
        )}

        {isError && (
          <div className="alert alert-danger d-flex align-items-center justify-content-between" role="alert">
            <div>{error instanceof Error ? error.message : t("Failed to load accounts")}</div>
            <Button variant="outline-danger" size="sm" onClick={() => void refetch()}>
              {t("Retry")}
            </Button>
          </div>
        )}

        {!isLoading && !isError && filteredAccounts.length === 0 && (
          <div className="text-center py-5 text-muted">
            <User size={48} className="mb-3 opacity-50" />
            <h5>{t("No tax accounts found")}</h5>
            <p className="small mb-0">
              {search
                ? t("No accounts match your search query.")
                : t("You do not have any registered tax accounts for this entity.")}
            </p>
          </div>
        )}

        <Row className="g-3">
          {filteredAccounts.map((account) => {
            const ownerLogo =
              account.owner_logo ||
              (account.owner_type === "corporation"
                ? corporationImageUrl(account.owner_id, 64)
                : allianceImageUrl(account.owner_id, 64));

            const charPortrait =
              account.character_portrait ||
              (account.character_id
                ? characterImageUrl(account.character_id, 64)
                : undefined);

            const isPaid = account.has_paid;

            return (
              <Col key={`${account.owner_type}-${account.owner_id}-${account.id}`} xs={12} lg={6}>
                <div className="aa-panel h-100 d-flex flex-column justify-content-between p-3 border-secondary">
                  <div>
                    {/* Header: Owner branding + Paid status badge */}
                    <div className="d-flex align-items-center justify-content-between gap-3 mb-3 pb-3 border-bottom border-secondary">
                      <div className="d-flex align-items-center gap-3">
                        <img
                          src={ownerLogo}
                          alt={account.owner_name}
                          width={48}
                          height={48}
                          className="rounded border border-secondary"
                        />
                        <div>
                          <h5 className="mb-0 text-light fw-bold">{account.owner_name}</h5>
                          <div className="d-flex align-items-center gap-2 mt-1">
                            <span className="aa-badge aa-badge-secondary">
                              {account.owner_type === "corporation"
                                ? t("Corporation")
                                : t("Alliance")}
                            </span>
                            <span className="aa-badge aa-badge-secondary">
                              {account.status_display}
                            </span>
                          </div>
                        </div>
                      </div>

                      <div>
                        {isPaid ? (
                          <span className="aa-badge aa-badge-success d-inline-flex align-items-center gap-1">
                            <CheckCircle size={14} />
                            {t("Paid")}
                          </span>
                        ) : (
                          <span className="aa-badge aa-badge-danger d-inline-flex align-items-center gap-1">
                            <AlertCircle size={14} />
                            {t("Unpaid / Due")}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Character Identity */}
                    <div className="d-flex align-items-center gap-3 mb-3 p-2 rounded bg-dark border border-secondary">
                      {charPortrait ? (
                        <img
                          src={charPortrait}
                          alt={account.character_name || account.name}
                          width={40}
                          height={40}
                          className="rounded-circle border border-secondary"
                        />
                      ) : (
                        <div
                          className="rounded-circle bg-secondary d-flex align-items-center justify-content-center"
                          style={{ width: 40, height: 40 }}
                        >
                          <User size={20} />
                        </div>
                      )}
                      <div>
                        <div className="small text-muted">{t("Linked Character")}</div>
                        <div className="fw-semibold text-light">
                          {account.character_name || account.name}
                        </div>
                      </div>
                    </div>

                    {/* Financial Metrics */}
                    <Row className="g-2 mb-3">
                      <Col sm={6}>
                        <div className="p-2 rounded bg-dark border border-secondary">
                          <div className="d-flex align-items-center gap-1 small text-muted mb-1">
                            <Wallet size={14} />
                            <span>{t("Current Balance")}</span>
                          </div>
                          <div className={`fs-5 fw-mono ${account.deposit > 0 ? "text-success" : "text-light"}`}>
                            {formatNumber(account.deposit)}
                          </div>
                        </div>
                      </Col>

                      <Col sm={6}>
                        <div className="p-2 rounded bg-dark border border-secondary">
                          <div className="d-flex align-items-center gap-1 small text-muted mb-1">
                            <CreditCard size={14} />
                            <span>{t("Tax Rate")}</span>
                          </div>
                          <div className="fs-5 fw-mono text-light">
                            {formatNumber(account.tax_amount)}
                            <span className="fs-6 text-muted ms-1">
                              / {account.tax_period} {t("Days")}
                            </span>
                          </div>
                        </div>
                      </Col>

                      <Col sm={6}>
                        <div className="p-2 rounded bg-dark border border-secondary">
                          <div className="d-flex align-items-center gap-1 small text-muted mb-1">
                            <Calendar size={14} />
                            <span>{t("Next Due")}</span>
                          </div>
                          <div className={`fw-semibold ${isPaid ? "text-light" : "text-danger"}`}>
                            {account.next_due ? (
                              <>
                                <span>{account.next_due}</span>
                                <div className="small text-muted">{formatRelativeTime(account.next_due)}</div>
                              </>
                            ) : (
                              <span className="text-muted">—</span>
                            )}
                          </div>
                        </div>
                      </Col>

                      <Col sm={6}>
                        <div className="p-2 rounded bg-dark border border-secondary">
                          <div className="d-flex align-items-center gap-1 small text-muted mb-1">
                            <Clock size={14} />
                            <span>{t("Last Payment")}</span>
                          </div>
                          <div className="fw-semibold text-light">
                            {account.last_paid ? (
                              <>
                                <span>{account.last_paid}</span>
                                <div className="small text-muted">{formatRelativeTime(account.last_paid)}</div>
                              </>
                            ) : (
                              <span className="text-muted">{t("Never")}</span>
                            )}
                          </div>
                        </div>
                      </Col>
                    </Row>

                    {/* Member details / Notice if present */}
                    {(account.joined || account.last_login || account.notice) && (
                      <div className="small text-muted p-2 rounded bg-dark border border-secondary mb-3">
                        <div className="d-flex flex-wrap gap-3">
                          {account.joined && (
                            <div>
                              <span className="text-secondary">{t("Joined")}:</span>{" "}
                              <span className="text-light">{formatRelativeTime(account.joined)}</span>
                            </div>
                          )}
                          {account.last_login && (
                            <div>
                              <span className="text-secondary">{t("Last Login")}:</span>{" "}
                              <span className="text-light">{formatRelativeTime(account.last_login)}</span>
                            </div>
                          )}
                        </div>
                        {account.notice && (
                          <div className="mt-1 pt-1 border-top border-secondary text-info">
                            <strong>{t("Notice")}:</strong> {account.notice}
                          </div>
                        )}
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="d-flex flex-wrap gap-2 pt-3 border-top border-secondary">
                    <Link
                      to={`/taxsystem/my-payments/${account.owner_id}/`}
                      className="aa-btn aa-btn-sm aa-btn-secondary flex-fill d-flex align-items-center justify-content-center gap-1"
                    >
                      <FileText size={14} />
                      {t("My Payments")}
                    </Link>
                    <Link
                      to={`/taxsystem/payments/${account.owner_id}/`}
                      className="aa-btn aa-btn-sm aa-btn-primary flex-fill d-flex align-items-center justify-content-center gap-1"
                    >
                      <CreditCard size={14} />
                      {t("Payments")}
                    </Link>
                    {account.open_invoices > 0 && (
                      <Badge bg="danger" className="d-flex align-items-center px-2">
                        {account.open_invoices} {t("Open")}
                      </Badge>
                    )}
                  </div>
                </div>
              </Col>
            );
          })}
        </Row>
      </div>
    </main>
  );
}

export default AccountOverviewPage;
