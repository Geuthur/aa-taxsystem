// React
import type { ReactNode } from "react";

// Third Party
import { Wallet } from "lucide-react";
import { Badge, Card, Col, ProgressBar, Row, Table } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// AA TaxSystem
import type { components } from "@/Api/OpenApi";
import { BaseModal, ModalSize } from "@/Components/Base/BaseModal";
import { formatNumber } from "@/Utils";

type DivisionsData = components["schemas"]["DashboardDivisionsSchema"];

interface DivisionsModalProps {
  show: boolean;
  onHide: () => void;
  divisions: DivisionsData;
}

export function DivisionsModal({ show, onHide, divisions }: DivisionsModalProps) {
  const { t } = useTranslation();
  const list = divisions.divisions || [];
  const total = divisions.total_balance || 0;

  const modalTitle: ReactNode = (
    <div className="d-flex align-items-center gap-2 text-success">
      <Wallet size={22} />
      <span>{t("Corporate Wallet Divisions", "Corporate Wallet Divisions")}</span>
    </div>
  );

  return (
    <BaseModal
      show={show}
      onHide={onHide}
      title={modalTitle}
      size={ModalSize.large}
      closeText={t("Close", "Close")}
    >
      <div className="mb-3">
        <Card className="bg-dark border-secondary">
          <Card.Body className="p-3">
            <Row className="align-items-center">
              <Col xs={12} sm={6}>
                <div className="text-muted small mb-1">{t("Total Wallet Balance", "Total Wallet Balance")}</div>
                <h4 className="text-success fw-bold mb-0">{formatNumber(total)} ISK</h4>
              </Col>
              <Col xs={12} sm={6} className="text-sm-end mt-2 mt-sm-0">
                <Badge bg="secondary" className="px-3 py-2">
                  {list.length} {t("Divisions", "Divisions")}
                </Badge>
              </Col>
            </Row>
          </Card.Body>
        </Card>
      </div>

      {list.length === 0 ? (
        <div className="text-center text-muted py-4">
          {t("No wallet divisions found.", "No wallet divisions found.")}
        </div>
      ) : (
        <div className="table-responsive">
          <Table hover variant="dark" className="align-middle mb-0 border-secondary">
            <thead className="text-muted small border-secondary">
              <tr>
                <th style={{ width: "60px" }}>#</th>
                <th>{t("Division Name", "Division Name")}</th>
                <th className="text-end">{t("Balance", "Balance")}</th>
                <th style={{ width: "120px" }} className="text-end">
                  {t("Share", "Share")}
                </th>
              </tr>
            </thead>
            <tbody>
              {list.map((div, idx) => {
                const sharePercent = total > 0 ? Math.max(0, Math.min(100, (div.balance / total) * 100)) : 0;
                return (
                  <tr key={`${div.name}-${idx}`}>
                    <td className="text-muted small fw-bold">{idx + 1}</td>
                    <td className="fw-semibold text-light">{div.name}</td>
                    <td className="text-end fw-bold text-success font-monospace">
                      {formatNumber(div.balance)} ISK
                    </td>
                    <td className="text-end">
                      <div className="d-flex align-items-center justify-content-end gap-2">
                        <span className="small text-muted font-monospace">
                          {sharePercent.toFixed(1)}%
                        </span>
                        <div style={{ width: "50px" }}>
                          <ProgressBar
                            now={sharePercent}
                            variant={sharePercent > 50 ? "success" : "info"}
                            style={{ height: "6px" }}
                          />
                        </div>
                      </div>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </Table>
        </div>
      )}
    </BaseModal>
  );
}

export default DivisionsModal;
