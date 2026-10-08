// React
import { useState } from "react";
import { Link, useParams } from "react-router-dom";

// Third Party
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Activity,
  ArrowLeft,
  BarChart3,
  Calendar,
  DollarSign,
  Edit,
  Filter,
  History,
  Layers,
  Settings,
  Users,
  Wallet,
} from "lucide-react";
import { Badge, Button, Card, Col, Form, Nav, Row, Spinner } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// AA TaxSystem
import {
  loadDashboard,
  updateTaxAmount,
  updateTaxPeriod,
} from "@/Api/ApiCalls";
import { queryKeys } from "@/Api/query";
import BaseSectionHeader from "@/Components/Base/BaseHeader";
import { BaseModal, ModalSize } from "@/Components/Base/BaseModal";
import { useOwnerTabState } from "@/Hooks/useTaxsystemState";
import DivisionsModal from "@/Pages/Manage/Modals/DivisionsModal";
import AccountsTab from "@/Pages/Manage/Tabs/AccountsTab";
import FiltersTab from "@/Pages/Manage/Tabs/FiltersTab";
import GroupsTab from "@/Pages/Manage/Tabs/GroupsTab";
import HistoryTab from "@/Pages/Manage/Tabs/HistoryTab";
import MembersTab from "@/Pages/Manage/Tabs/MembersTab";
import { formatNumber } from "@/Utils";

export function OwnerManagePage() {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const { ownerId } = useParams<{ ownerId: string }>();
  const numericOwnerId = Number(ownerId || 0);

  const [activeTab, setActiveTab] = useOwnerTabState();

  // Modal states
  const [showSettingsModal, setShowSettingsModal] = useState(false);
  const [showDivisionsModal, setShowDivisionsModal] = useState(false);
  const [newTaxAmount, setNewTaxAmount] = useState<number>(0);
  const [newTaxPeriod, setNewTaxPeriod] = useState<number>(0);

  const { data: dashboard, isLoading, isError, error } = useQuery({
    queryKey: queryKeys.Dashboard(numericOwnerId),
    queryFn: () => loadDashboard(numericOwnerId),
    enabled: numericOwnerId > 0,
  });

  const taxAmountMutation = useMutation({
    mutationFn: (val: number) => updateTaxAmount(numericOwnerId, val),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.Dashboard(numericOwnerId) });
    },
  });

  const taxPeriodMutation = useMutation({
    mutationFn: (val: number) => updateTaxPeriod(numericOwnerId, val),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.Dashboard(numericOwnerId) });
    },
  });

  const handleOpenSettings = () => {
    if (dashboard) {
      setNewTaxAmount(dashboard.tax_amount);
      setNewTaxPeriod(dashboard.tax_period);
      setShowSettingsModal(true);
    }
  };

  const handleSaveSettings = async () => {
    if (newTaxAmount !== dashboard?.tax_amount) {
      await taxAmountMutation.mutateAsync(newTaxAmount);
    }
    if (newTaxPeriod !== dashboard?.tax_period) {
      await taxPeriodMutation.mutateAsync(newTaxPeriod);
    }
    setShowSettingsModal(false);
  };

  if (isLoading) {
    return (
      <main className="text-center py-5">
        <Spinner animation="border" variant="primary" />
        <div className="mt-2 text-muted">{t("Loading dashboard...")}</div>
      </main>
    );
  }

  if (isError || !dashboard) {
    return (
      <main className="alert alert-danger" role="alert">
        {error instanceof Error ? error.message : t("Failed to load dashboard")}
      </main>
    );
  }

  const isCorp = dashboard.owner.owner_type === "corporation";

  return (
    <main>
      <BaseSectionHeader name={dashboard.owner.owner_name}>
        <div className="d-flex align-items-center gap-2">
          <Link to="/" className="aa-btn aa-btn-sm aa-btn-secondary d-flex align-items-center gap-1">
            <ArrowLeft size={14} />
            {t("Overview")}
          </Link>
          <Button
            variant="outline-warning"
            size="sm"
            className="d-flex align-items-center gap-1"
            onClick={handleOpenSettings}
          >
            <Settings size={14} />
            {t("Tax Settings")}
          </Button>
        </div>
      </BaseSectionHeader>

      {/* Top Metric Cards */}
      <Row className="g-3 mt-1 mb-3">
        <Col xs={12} sm={6} lg={3}>
          <Card className="bg-dark border-secondary h-100 shadow-sm">
            <Card.Body className="p-3 d-flex flex-column justify-content-between">
              <div>
                <div className="d-flex justify-content-between align-items-center mb-2">
                  <span className="text-muted small fw-semibold">{t("Tax Configuration")}</span>
                  <div className="p-2 rounded-3 bg-primary bg-opacity-10 text-primary">
                    <DollarSign size={24} />
                  </div>
                </div>
                <h4 className="mb-1 text-light fw-bold">
                  {formatNumber(dashboard.tax_amount)} / {dashboard.tax_period} {t("Days")}
                </h4>
                <div className="text-muted small">
                  {t("Fixed tax amount & billing period")}
                </div>
              </div>
            </Card.Body>
          </Card>
        </Col>

        <Col xs={12} sm={6} lg={3}>
          <Card className="bg-dark border-secondary h-100 shadow-sm">
            <Card.Body className="p-3 d-flex flex-column justify-content-between">
              <div>
                <div className="d-flex justify-content-between align-items-center mb-2">
                  <span className="text-muted small fw-semibold">{t("Total Wallet Balance")}</span>
                  <div className="p-2 rounded-3 bg-success bg-opacity-10 text-success">
                    <Wallet size={24} />
                  </div>
                </div>
                <h4 className="mb-1 text-success fw-bold">
                  {formatNumber(dashboard.divisions.total_balance)}
                </h4>
                <div className="text-muted small">
                  {dashboard.divisions.divisions.length} {t("divisions monitored")}
                </div>
              </div>
              <Button
                variant="outline-success"
                size="sm"
                className="mt-3 w-100 d-flex align-items-center justify-content-center gap-1"
                onClick={() => setShowDivisionsModal(true)}
              >
                <Layers size={14} />
                {t("View Divisions")}
              </Button>
            </Card.Body>
          </Card>
        </Col>

        <Col xs={12} sm={6} lg={3}>
          <Card className="bg-dark border-secondary h-100 shadow-sm">
            <Card.Body className="p-3 d-flex flex-column justify-content-between">
              <div>
                <div className="d-flex justify-content-between align-items-center mb-2">
                  <span className="text-muted small fw-semibold">{t("30-Day Activity")}</span>
                  <div className="p-2 rounded-3 bg-info bg-opacity-10 text-info">
                    <Activity size={24} />
                  </div>
                </div>
                <h4 className="mb-1 text-info fw-bold">
                  {formatNumber(dashboard.activity)}
                </h4>
                <div className="text-muted small">
                  {t("Total journal volume (30d)")}
                </div>
              </div>
            </Card.Body>
          </Card>
        </Col>

        <Col xs={12} sm={6} lg={3}>
          <Card className="bg-dark border-secondary h-100 shadow-sm">
            <Card.Body className="p-3 d-flex flex-column justify-content-between">
              <div>
                <div className="d-flex justify-content-between align-items-center mb-2">
                  <span className="text-muted small fw-semibold">{t("Update Status")}</span>
                  <div className="p-2 rounded-3 bg-warning bg-opacity-10 text-warning">
                    <Calendar size={24} />
                  </div>
                </div>
                <h5 className="mb-1">
                  <Badge bg="success" className="text-uppercase">
                    {dashboard.update_status.status ? t("Synchronized") : t("Pending")}
                  </Badge>
                </h5>
                <div className="text-muted small">
                  {t("ESI synchronization status")}
                </div>
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* System Statistics Summary */}
      {dashboard.statistics && (
        <Card className="bg-dark border-secondary mb-4 shadow-sm">
          <Card.Header className="border-secondary py-2 bg-transparent">
            <h6 className="mb-0 text-light fw-bold d-flex align-items-center gap-2">
              <BarChart3 size={18} className="text-primary" />
              {t("System Statistics")}
            </h6>
          </Card.Header>
          <Card.Body className="p-3">
            <Row className="g-3">
              <Col xs={6} sm={4} md={2}>
                <div className="p-2 rounded bg-black bg-opacity-25 border border-secondary text-center">
                  <div className="text-muted small mb-1">{t("Pending")}</div>
                  <h4 className="text-warning fw-bold mb-0">
                    {dashboard.statistics.payments?.payments_pending ?? 0}
                  </h4>
                </div>
              </Col>
              <Col xs={6} sm={4} md={2}>
                <div className="p-2 rounded bg-black bg-opacity-25 border border-secondary text-center">
                  <div className="text-muted small mb-1">{t("Approved")}</div>
                  <h4 className="text-success fw-bold mb-0">
                    {dashboard.statistics.payments?.payments_approved ?? 0}
                  </h4>
                </div>
              </Col>
              <Col xs={6} sm={4} md={2}>
                <div className="p-2 rounded bg-black bg-opacity-25 border border-secondary text-center">
                  <div className="text-muted small mb-1">{t("Automatic")}</div>
                  <h4 className="text-info fw-bold mb-0">
                    {dashboard.statistics.payments?.payments_automatic ?? 0}
                  </h4>
                </div>
              </Col>
              <Col xs={6} sm={4} md={2}>
                <div className="p-2 rounded bg-black bg-opacity-25 border border-secondary text-center">
                  <div className="text-muted small mb-1">{t("Manual")}</div>
                  <h4 className="text-light fw-bold mb-0">
                    {dashboard.statistics.payments?.payments_manual ?? 0}
                  </h4>
                </div>
              </Col>
              <Col xs={6} sm={4} md={2}>
                <div className="p-2 rounded bg-black bg-opacity-25 border border-secondary text-center">
                  <div className="text-muted small mb-1">{t("Active Accounts")}</div>
                  <h4 className="text-success fw-bold mb-0">
                    {dashboard.statistics.tax_account?.accounts_active ?? 0}
                  </h4>
                </div>
              </Col>
              <Col xs={6} sm={4} md={2}>
                <div className="p-2 rounded bg-black bg-opacity-25 border border-secondary text-center">
                  <div className="text-muted small mb-1">{t("Unpaid Accounts")}</div>
                  <h4 className="text-danger fw-bold mb-0">
                    {dashboard.statistics.tax_account?.accounts_unpaid ?? 0}
                  </h4>
                </div>
              </Col>
            </Row>
          </Card.Body>
        </Card>
      )}

      {/* Tabs Section */}
      <div className="p-3 aa-panel rounded">
        <Nav variant="tabs" className="border-secondary mb-3">
          <Nav.Item>
            <Nav.Link
              active={activeTab === "accounts"}
              onClick={() => setActiveTab("accounts")}
              className="d-flex align-items-center gap-2"
            >
              <Users size={16} />
              {t("Tax Accounts")}
            </Nav.Link>
          </Nav.Item>
          {isCorp && (
            <Nav.Item>
              <Nav.Link
                active={activeTab === "members"}
                onClick={() => setActiveTab("members")}
                className="d-flex align-items-center gap-2"
              >
                <Layers size={16} />
                {t("Members")}
              </Nav.Link>
            </Nav.Item>
          )}
          <Nav.Item>
            <Nav.Link
              active={activeTab === "filters"}
              onClick={() => setActiveTab("filters")}
              className="d-flex align-items-center gap-2"
            >
              <Filter size={16} />
              {t("Filters")}
            </Nav.Link>
          </Nav.Item>
          <Nav.Item>
            <Nav.Link
              active={activeTab === "groups"}
              onClick={() => setActiveTab("groups")}
              className="d-flex align-items-center gap-2"
            >
              <Settings size={16} />
              {t("Groups")}
            </Nav.Link>
          </Nav.Item>
          <Nav.Item>
            <Nav.Link
              active={activeTab === "history"}
              onClick={() => setActiveTab("history")}
              className="d-flex align-items-center gap-2"
            >
              <History size={16} />
              {t("History")}
            </Nav.Link>
          </Nav.Item>
        </Nav>

        {activeTab === "accounts" && <AccountsTab ownerId={numericOwnerId} />}
        {activeTab === "members" && isCorp && <MembersTab ownerId={numericOwnerId} />}
        {activeTab === "filters" && <FiltersTab ownerId={numericOwnerId} />}
        {activeTab === "groups" && <GroupsTab ownerId={numericOwnerId} />}
        {activeTab === "history" && <HistoryTab ownerId={numericOwnerId} />}
      </div>

      {/* Tax Configuration Modal via BaseModal */}
      <BaseModal
        show={showSettingsModal}
        onHide={() => setShowSettingsModal(false)}
        size={ModalSize.medium}
        title={
          <div className="d-flex align-items-center gap-2 text-warning">
            <Edit size={20} />
            <span>{t("Edit Tax Settings")}</span>
          </div>
        }
        footer={
          <>
            <Button variant="secondary" onClick={() => setShowSettingsModal(false)}>
              {t("Cancel")}
            </Button>
            <Button
              variant="primary"
              disabled={taxAmountMutation.isPending || taxPeriodMutation.isPending}
              onClick={handleSaveSettings}
            >
              {(taxAmountMutation.isPending || taxPeriodMutation.isPending) && (
                <Spinner size="sm" animation="border" className="me-1" />
              )}
              {t("Save Settings")}
            </Button>
          </>
        }
      >
        <Form.Group className="mb-3">
          <Form.Label>{t("Tax Amount (ISK)")}</Form.Label>
          <Form.Control
            type="number"
            step="0.01"
            min="0"
            value={newTaxAmount}
            onChange={(e) => setNewTaxAmount(parseFloat(e.target.value) || 0)}
            className="bg-dark text-light border-secondary"
          />
        </Form.Group>
        <Form.Group className="mb-3">
          <Form.Label>{t("Tax Period (Days)")}</Form.Label>
          <Form.Control
            type="number"
            min="1"
            value={newTaxPeriod}
            onChange={(e) => setNewTaxPeriod(parseInt(e.target.value, 10) || 1)}
            className="bg-dark text-light border-secondary"
          />
        </Form.Group>
      </BaseModal>

      {/* Corporate Wallet Divisions Modal via BaseModal */}
      <DivisionsModal
        show={showDivisionsModal}
        onHide={() => setShowDivisionsModal(false)}
        divisions={dashboard.divisions}
      />
    </main>
  );
}

export default OwnerManagePage;
