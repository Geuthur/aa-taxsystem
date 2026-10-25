// React
import { useState } from "react";
import { Link } from "react-router-dom";

// Third Party
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  AlertTriangle,
  ArrowLeft,
  Building2,
  ChevronDown,
  ChevronUp,
  Play,
  RefreshCw,
  Shield,
  ShieldAlert,
} from "lucide-react";
import { parseAsInteger, parseAsString, useQueryState } from "nuqs";
import { Alert, Button, Card, Col, Form, Modal, Row, Spinner } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// AA TaxSystem
import {
  deleteAdministrationOwner,
  loadAdministrationOwners,
  loadUserData,
  runAdminTasks,
  triggerAdministrationOwnerUpdate,
} from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";
import type { AdministrationTaxOwnerSchema } from "@/Api/schema";
import AdministrationInspectionView from "@/Components/Administration/AdministrationInspectionView";
import AdministrationOwnersTable from "@/Components/Administration/AdministrationOwnersTable";
import { ButtonGroupFilter } from "@/Components/Buttons/ButtonGroupFilter";
import styles from "@/Styles/modules/Administration.module.css";

type TypeFilter = "all" | "corporation" | "alliance" | "issues";

export function AdministrationPage() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();

  // nuqs query state for inspection view
  const [inspectId, setInspectId] = useQueryState("inspect", parseAsInteger);
  const [inspectType, setInspectType] = useQueryState("type", parseAsString);

  // Filter states
  const [typeFilter, setTypeFilter] = useState<TypeFilter>("all");
  const [searchTerm, setSearchTerm] = useState("");

  // Global Task states
  const [showTaskPanel, setShowTaskPanel] = useState(false);
  const [forceRefreshGlobal, setForceRefreshGlobal] = useState(false);
  const [corpIdInput, setCorpIdInput] = useState("");
  const [allyIdInput, setAllyIdInput] = useState("");

  // Feedback messages
  const [message, setMessage] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Delete modal state
  const [ownerToDelete, setOwnerToDelete] = useState<AdministrationTaxOwnerSchema | null>(null);

  // Current user, the global tasks and force refresh are reserved for superusers
  const { data: userData } = useQuery({
    queryKey: queryKeys.User,
    queryFn: loadUserData,
  });
  const isSuperuser = Boolean(userData?.user.is_superuser);

  // Queries
  const {
    data: owners = [],
    isLoading,
    isError,
    error,
  } = useQuery({
    queryKey: queryKeys.AdministrationOwners,
    queryFn: loadAdministrationOwners,
  });

  // Global Task Mutation
  const globalTaskMutation = useMutation({
    mutationFn: (vars: Parameters<typeof runAdminTasks>[0]) => runAdminTasks(vars),
    onSuccess: (data) => {
      setMessage(data.message);
      setErrorMsg(null);
    },
    onError: (err: Error) => {
      setErrorMsg(err.message);
      setMessage(null);
    },
  });

  // Individual Owner Update Mutation
  const updateMutation = useMutation({
    mutationFn: (vars: Parameters<typeof triggerAdministrationOwnerUpdate>[0]) =>
      triggerAdministrationOwnerUpdate(vars),
    onSuccess: (data) => {
      setMessage(data.message);
      setErrorMsg(null);
      queryClient.invalidateQueries({ queryKey: queryKeys.AdministrationOwners });
    },
    onError: (err: Error) => {
      setErrorMsg(err.message);
      setMessage(null);
    },
  });

  // Delete Owner Mutation
  const deleteMutation = useMutation({
    mutationFn: (vars: Parameters<typeof deleteAdministrationOwner>[0]) =>
      deleteAdministrationOwner(vars),
    onSuccess: (data) => {
      setMessage(data.message);
      setErrorMsg(null);
      setOwnerToDelete(null);
      queryClient.invalidateQueries({ queryKey: queryKeys.AdministrationOwners });
    },
    onError: (err: Error) => {
      setErrorMsg(err.message);
      setMessage(null);
    },
  });

  // If inspection view active
  if (inspectId) {
    return (
      <AdministrationInspectionView
        ownerId={inspectId}
        ownerType={inspectType || "corporation"}
        onBack={() => {
          setInspectId(null);
          setInspectType(null);
        }}
      />
    );
  }

  // Filter owners
  const filteredOwners = owners.filter((owner) => {
    if (typeFilter !== "all") {
      if (typeFilter === "issues") {
        const hasIssue =
          owner.status === "error" ||
          owner.status === "token_error" ||
          Boolean(owner.error_message);
        if (!hasIssue) return false;
      } else if (owner.owner_type !== typeFilter) {
        return false;
      }
    }
    if (searchTerm.trim()) {
      const term = searchTerm.toLowerCase();
      const matchName = owner.name.toLowerCase().includes(term);
      const matchTicker = owner.ticker?.toLowerCase().includes(term) ?? false;
      return matchName || matchTicker;
    }
    return true;
  });

  // Metrics
  const totalCount = owners.length;
  const corpCount = owners.filter((o) => o.owner_type === "corporation").length;
  const allianceCount = owners.filter((o) => o.owner_type === "alliance").length;
  const errorCount = owners.filter(
    (o) => o.status === "error" || o.status === "token_error" || Boolean(o.error_message),
  ).length;

  return (
    <Card className="bg-dark d-flex flex-column gap-3">
      <Card.Body>
        <header className="d-flex align-items-center justify-content-between gap-3 mb-4">
          <div className="d-flex align-items-center gap-3">
            <div className="p-2 rounded bg-danger-subtle text-danger border border-danger-subtle">
              <ShieldAlert size={28} />
            </div>
            <div>
              <h1 className="h3 mb-1 fw-bold">{t("Administration")}</h1>
              <p className="mb-0 small text-muted">
                {t(
                  "System-wide tax owner administration, synchronization tasks, and compliance monitoring.",
                )}
              </p>
            </div>
          </div>
          <Link
            to="/"
            className="btn btn-sm btn-secondary d-flex align-items-center gap-1"
          >
            <ArrowLeft size={14} />
            {t("Overview")}
          </Link>
        </header>

        {/* Alert Messages */}
        {message && (
          <Alert
            variant="success"
            className="mt-3"
            onClose={() => setMessage(null)}
            dismissible
          >
            <span data-testid="task-feedback-message">{message}</span>
          </Alert>
        )}
        {errorMsg && (
          <Alert
            variant="danger"
            className="mt-3"
            onClose={() => setErrorMsg(null)}
            dismissible
          >
            <span data-testid="task-feedback-message">{errorMsg}</span>
          </Alert>
        )}
        {isError && (
          <Alert variant="danger" className="mt-3">
            {error instanceof Error ? error.message : t("Failed to load administration data")}
          </Alert>
        )}

        {/* Metrics Row */}
        <Row className="g-3 mt-1 mb-3">
          <Col xs={12} sm={6} md={3}>
            <Card className="bg-body border-secondary h-100 shadow-sm">
              <Card.Body className="p-3 d-flex align-items-center justify-content-between">
                <div>
                  <span className="text-muted small fw-semibold">{t("Total Owners")}</span>
                  <h4 className="mb-0 text-light fw-bold">{totalCount}</h4>
                </div>
                <div className="p-2 rounded-3 bg-secondary bg-opacity-25 text-light">
                  <Shield size={24} />
                </div>
              </Card.Body>
            </Card>
          </Col>

          <Col xs={12} sm={6} md={3}>
            <Card className="bg-body border-secondary h-100 shadow-sm">
              <Card.Body className="p-3 d-flex align-items-center justify-content-between">
                <div>
                  <span className="text-muted small fw-semibold">{t("Corporations")}</span>
                  <h4 className="mb-0 text-primary fw-bold">{corpCount}</h4>
                </div>
                <div className="p-2 rounded-3 bg-primary bg-opacity-10 text-primary">
                  <Building2 size={24} />
                </div>
              </Card.Body>
            </Card>
          </Col>

          <Col xs={12} sm={6} md={3}>
            <Card className="bg-body border-secondary h-100 shadow-sm">
              <Card.Body className="p-3 d-flex align-items-center justify-content-between">
                <div>
                  <span className="text-muted small fw-semibold">{t("Alliances")}</span>
                  <h4 className="mb-0 text-info fw-bold">{allianceCount}</h4>
                </div>
                <div className="p-2 rounded-3 bg-info bg-opacity-10 text-info">
                  <Shield size={24} />
                </div>
              </Card.Body>
            </Card>
          </Col>

          <Col xs={12} sm={6} md={3}>
            <Card className="bg-body border-secondary h-100 shadow-sm">
              <Card.Body className="p-3 d-flex align-items-center justify-content-between">
                <div>
                  <span className="text-muted small fw-semibold">{t("Sync Issues")}</span>
                  <h4 className={`mb-0 fw-bold ${errorCount > 0 ? "text-danger" : "text-success"}`}>
                    {errorCount}
                  </h4>
                </div>
                <div
                  className={`p-2 rounded-3 ${errorCount > 0 ? "bg-danger bg-opacity-10 text-danger" : "bg-success bg-opacity-10 text-success"
                    }`}
                >
                  {errorCount > 0 ? <AlertTriangle size={24} /> : <Shield size={24} />}
                </div>
              </Card.Body>
            </Card>
          </Col>
        </Row>

        {/* Global Task Administration Panel (Collapsible) */}
        {isSuperuser && (
          <Card className="bg-dark border-secondary mb-4 shadow-sm">
            <Card.Header
              className={`border-secondary d-flex align-items-center justify-content-between py-2 ${styles.cursorPointer}`}
              onClick={() => setShowTaskPanel((prev) => !prev)}
            >
              <div className="d-flex align-items-center gap-2">
                <RefreshCw size={16} className="text-primary" />
                <span className="fw-semibold text-light">{t("Global Task Administration")}</span>
              </div>
              <Button
                variant="link"
                size="sm"
                className="p-0 text-muted"
                aria-label={t("Toggle Task Administration")}
                data-testid="toggle-task-panel"
                onClick={(e) => {
                  e.stopPropagation();
                  setShowTaskPanel((prev) => !prev);
                }}
              >
                {showTaskPanel ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
              </Button>
            </Card.Header>

            {showTaskPanel && (
              <Card.Body className="p-3">
                <Form.Group className="mb-3">
                  <Form.Check
                    type="switch"
                    id="global-force-refresh"
                    label={<span className="small text-muted">{t("Force Refresh ESI")}</span>}
                    checked={forceRefreshGlobal}
                    onChange={(e) => setForceRefreshGlobal(e.target.checked)}
                  />
                </Form.Group>

                <Row className="g-3">
                  <Col md={4}>
                    <Card className="bg-dark border-secondary h-100">
                      <Card.Header className="border-secondary py-2">
                        <h6 className="mb-0 text-light">{t("All Tax Systems")}</h6>
                      </Card.Header>
                      <Card.Body className="d-flex flex-column justify-content-between p-3">
                        <p className="text-muted small">
                          {t("Queue background tasks to synchronize all active corporations and alliances.")}
                        </p>
                        <Button
                          variant="primary"
                          size="sm"
                          disabled={globalTaskMutation.isPending}
                          onClick={() =>
                            globalTaskMutation.mutate({
                              target: "all",
                              force_refresh: forceRefreshGlobal,
                            })
                          }
                          className="w-100 d-flex align-items-center justify-content-center gap-1"
                        >
                          {globalTaskMutation.isPending ? (
                            <Spinner size="sm" animation="border" />
                          ) : (
                            <Play size={14} />
                          )}
                          {t("Update All")}
                        </Button>
                      </Card.Body>
                    </Card>
                  </Col>

                  <Col md={4}>
                    <Card className="bg-dark border-secondary h-100">
                      <Card.Header className="border-secondary py-2">
                        <h6 className="mb-0 text-light">{t("Corporations")}</h6>
                      </Card.Header>
                      <Card.Body className="d-flex flex-column justify-content-between p-3">
                        <Form.Group className="mb-2">
                          <Form.Control
                            size="sm"
                            type="number"
                            placeholder={t("All or specific Corp ID")}
                            value={corpIdInput}
                            onChange={(e) => setCorpIdInput(e.target.value)}
                            className="bg-dark text-light border-secondary"
                          />
                        </Form.Group>
                        <Button
                          variant="primary"
                          size="sm"
                          disabled={globalTaskMutation.isPending}
                          onClick={() =>
                            globalTaskMutation.mutate({
                              target: "corporation",
                              eve_id: corpIdInput ? parseInt(corpIdInput, 10) : undefined,
                              force_refresh: forceRefreshGlobal,
                            })
                          }
                          className="w-100 d-flex align-items-center justify-content-center gap-1"
                        >
                          {globalTaskMutation.isPending ? (
                            <Spinner size="sm" animation="border" />
                          ) : (
                            <Play size={14} />
                          )}
                          {corpIdInput ? t("Update Corp") : t("Update All Corps")}
                        </Button>
                      </Card.Body>
                    </Card>
                  </Col>

                  <Col md={4}>
                    <Card className="bg-dark border-secondary h-100">
                      <Card.Header className="border-secondary py-2">
                        <h6 className="mb-0 text-light">{t("Alliances")}</h6>
                      </Card.Header>
                      <Card.Body className="d-flex flex-column justify-content-between p-3">
                        <Form.Group className="mb-2">
                          <Form.Control
                            size="sm"
                            type="number"
                            placeholder={t("All or specific Alliance ID")}
                            value={allyIdInput}
                            onChange={(e) => setAllyIdInput(e.target.value)}
                            className="bg-dark text-light border-secondary"
                          />
                        </Form.Group>
                        <Button
                          variant="primary"
                          size="sm"
                          disabled={globalTaskMutation.isPending}
                          onClick={() =>
                            globalTaskMutation.mutate({
                              target: "alliance",
                              eve_id: allyIdInput ? parseInt(allyIdInput, 10) : undefined,
                              force_refresh: forceRefreshGlobal,
                            })
                          }
                          className="w-100 d-flex align-items-center justify-content-center gap-1"
                        >
                          {globalTaskMutation.isPending ? (
                            <Spinner size="sm" animation="border" />
                          ) : (
                            <Play size={14} />
                          )}
                          {allyIdInput ? t("Update Alliance") : t("Update All Alliances")}
                        </Button>
                      </Card.Body>
                    </Card>
                  </Col>
                </Row>
              </Card.Body>
            )}
          </Card>
        )}

        {/* Filter and Search Bar */}
        <div className="d-flex flex-column flex-md-row justify-content-between align-items-md-center gap-2 mb-3">
          <ButtonGroupFilter<TypeFilter>
            value={typeFilter}
            onChange={setTypeFilter}
            options={[
              { value: "all", label: t("All"), count: totalCount },
              { value: "corporation", label: t("Corporations"), count: corpCount },
              { value: "alliance", label: t("Alliances"), count: allianceCount },
              { value: "issues", label: t("Issues"), count: errorCount },
            ]}
            ariaLabel={t("Filter owners by type")}
          />

          <div className={styles.searchContainer}>
            <Form.Control
              type="search"
              placeholder={t("Search by name or ticker…")}
              size="sm"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="bg-dark text-light border-secondary"
            />
          </div>
        </div>

        {/* Owners Table */}
        <AdministrationOwnersTable
          data={filteredOwners}
          isLoading={isLoading}
          isUpdating={updateMutation.isPending}
          canForceRefresh={isSuperuser}
          onInspect={(owner) => {
            setInspectId(owner.owner_id);
            setInspectType(owner.owner_type);
          }}
          onUpdate={(owner, forceRefresh) => {
            updateMutation.mutate({
              ownerType: owner.owner_type,
              ownerId: owner.owner_id,
              payload: { force_refresh: forceRefresh },
            });
          }}
          onDelete={(owner) => setOwnerToDelete(owner)}
        />

        {/* Delete Confirmation Modal */}
        {ownerToDelete && (
          <Modal
            show={!!ownerToDelete}
            onHide={() => setOwnerToDelete(null)}
            centered
            className="modal-dark"
            contentClassName="aa-react"
          >
            <Modal.Header closeButton className="border-secondary">
              <Modal.Title className="text-danger d-flex align-items-center gap-2">
                <ShieldAlert size={20} />
                {t("Confirm Owner Deletion")}
              </Modal.Title>
            </Modal.Header>
            <Modal.Body>
              <p className="text-light">
                {t("Are you sure you want to delete {{name}} ({{type}})?", {
                  name: ownerToDelete.name,
                  type: ownerToDelete.owner_type,
                })}
              </p>
              <Alert variant="warning" className="small mb-0">
                {t(
                  "This action cannot be undone. All associated tax accounts, records, and configuration will be permanently deleted from the database.",
                )}
              </Alert>
            </Modal.Body>
            <Modal.Footer className="border-secondary">
              <Button
                variant="secondary"
                onClick={() => setOwnerToDelete(null)}
                disabled={deleteMutation.isPending}
                
              >
                {t("Cancel")}
              </Button>
              <Button
                variant="danger"
                disabled={deleteMutation.isPending}
                onClick={() => {
                  deleteMutation.mutate({
                    ownerType: ownerToDelete.owner_type,
                    ownerId: ownerToDelete.owner_id,
                  });
                }}
                className="d-flex align-items-center gap-1"
              >
                {deleteMutation.isPending && <Spinner size="sm" animation="border" />}
                {t("Delete Owner")}
              </Button>
            </Modal.Footer>
          </Modal>
        )}
      </Card.Body>
    </Card>
  );
}

export default AdministrationPage;
