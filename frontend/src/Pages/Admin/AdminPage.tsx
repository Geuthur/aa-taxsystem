// React
import { useState } from "react";
import { Link } from "react-router-dom";

// Third Party
import { useMutation } from "@tanstack/react-query";
import { ArrowLeft, Building2, Play, RefreshCw, Shield } from "lucide-react";
import { Alert, Button, Card, Col, Form, Row, Spinner } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// AA TaxSystem
import { runAdminTasks } from "@/Api/ApiCalls";
import BaseSectionHeader from "@/Components/Base/BaseHeader";

export function AdminPage() {
  const { t } = useTranslation();
  const [forceRefresh, setForceRefresh] = useState(false);
  const [corpIdInput, setCorpIdInput] = useState("");
  const [allyIdInput, setAllyIdInput] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const taskMutation = useMutation({
    mutationFn: runAdminTasks,
    onSuccess: (data) => {
      setMessage(data.message);
      setErrorMsg(null);
    },
    onError: (err: Error) => {
      setErrorMsg(err.message);
      setMessage(null);
    },
  });

  return (
    <main>
      <BaseSectionHeader name={t("Superuser Task Administration")}>
        <Link to="/" className="aa-btn aa-btn-sm aa-btn-secondary d-flex align-items-center gap-1">
          <ArrowLeft size={14} />
          {t("Overview")}
        </Link>
      </BaseSectionHeader>

      <div className="mt-3 p-3 aa-panel rounded">
        {message && (
          <Alert variant="success" onClose={() => setMessage(null)} dismissible>
            {message}
          </Alert>
        )}
        {errorMsg && (
          <Alert variant="danger" onClose={() => setErrorMsg(null)} dismissible>
            {errorMsg}
          </Alert>
        )}

        <Form.Group className="mb-4">
          <Form.Check
            type="checkbox"
            id="force-refresh"
            label={t("Force Refresh ESI (Bypass cache)")}
            checked={forceRefresh}
            onChange={(e) => setForceRefresh(e.target.checked)}
            className="text-light"
          />
        </Form.Group>

        <Row className="g-4">
          <Col md={4}>
            <Card className="bg-dark border-secondary h-100 shadow-sm">
              <Card.Header className="border-secondary d-flex align-items-center gap-2">
                <RefreshCw size={18} className="text-primary" />
                <h6 className="mb-0">{t("All Tax Systems")}</h6>
              </Card.Header>
              <Card.Body className="d-flex flex-column justify-content-between">
                <p className="text-muted small">
                  {t(
                    "Queue background tasks to synchronize all active corporations and alliances.",
                  )}
                </p>
                <Button
                  variant="primary"
                  disabled={taskMutation.isPending}
                  onClick={() =>
                    taskMutation.mutate({
                      target: "all",
                      force_refresh: forceRefresh,
                    })
                  }
                  className="w-100 d-flex align-items-center justify-content-center gap-1"
                >
                  {taskMutation.isPending ? <Spinner size="sm" animation="border" /> : <Play size={16} />}
                  {t("Update All")}
                </Button>
              </Card.Body>
            </Card>
          </Col>

          <Col md={4}>
            <Card className="bg-dark border-secondary h-100 shadow-sm">
              <Card.Header className="border-secondary d-flex align-items-center gap-2">
                <Building2 size={18} className="text-info" />
                <h6 className="mb-0">{t("Corporation Updates")}</h6>
              </Card.Header>
              <Card.Body className="d-flex flex-column justify-content-between">
                <div>
                  <p className="text-muted small">
                    {t(
                      "Synchronize all corporations or enter a specific Corporation ID.",
                    )}
                  </p>
                  <Form.Group className="mb-3">
                    <Form.Control
                      type="number"
                      placeholder={t("Optional Corporation ID")}
                      value={corpIdInput}
                      onChange={(e) => setCorpIdInput(e.target.value)}
                      className="bg-dark text-light border-secondary"
                    />
                  </Form.Group>
                </div>
                <Button
                  variant="info"
                  disabled={taskMutation.isPending}
                  onClick={() =>
                    taskMutation.mutate({
                      target: "corporation",
                      eve_id: corpIdInput ? parseInt(corpIdInput, 10) : undefined,
                      force_refresh: forceRefresh,
                    })
                  }
                  className="w-100 d-flex align-items-center justify-content-center gap-1 text-dark"
                >
                  {taskMutation.isPending ? <Spinner size="sm" animation="border" /> : <Play size={16} />}
                  {t("Update Corporation(s)")}
                </Button>
              </Card.Body>
            </Card>
          </Col>

          <Col md={4}>
            <Card className="bg-dark border-secondary h-100 shadow-sm">
              <Card.Header className="border-secondary d-flex align-items-center gap-2">
                <Shield size={18} className="text-warning" />
                <h6 className="mb-0">{t("Alliance Updates")}</h6>
              </Card.Header>
              <Card.Body className="d-flex flex-column justify-content-between">
                <div>
                  <p className="text-muted small">
                    {t(
                      "Synchronize all alliances or enter a specific Alliance ID.",
                    )}
                  </p>
                  <Form.Group className="mb-3">
                    <Form.Control
                      type="number"
                      placeholder={t("Optional Alliance ID")}
                      value={allyIdInput}
                      onChange={(e) => setAllyIdInput(e.target.value)}
                      className="bg-dark text-light border-secondary"
                    />
                  </Form.Group>
                </div>
                <Button
                  variant="warning"
                  disabled={taskMutation.isPending}
                  onClick={() =>
                    taskMutation.mutate({
                      target: "alliance",
                      eve_id: allyIdInput ? parseInt(allyIdInput, 10) : undefined,
                      force_refresh: forceRefresh,
                    })
                  }
                  className="w-100 d-flex align-items-center justify-content-center gap-1 text-dark"
                >
                  {taskMutation.isPending ? <Spinner size="sm" animation="border" /> : <Play size={16} />}
                  {t("Update Alliance(s)")}
                </Button>
              </Card.Body>
            </Card>
          </Col>
        </Row>
      </div>
    </main>
  );
}

export default AdminPage;
