// React
import { useMemo, useState } from "react";

// Third Party
import type { ColumnDef } from "@tanstack/react-table";
import { Eye, RefreshCw, Trash2 } from "lucide-react";
import { Badge, Button, ButtonGroup, Dropdown, Spinner } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// AA TaxSystem
import type { AdministrationTaxOwnerSchema } from "@/Api/schema";
import { AdministrationErrorModal } from "@/Components/Administration/AdministrationErrorModal";
import { AdministrationStatusBadge } from "@/Components/Administration/AdministrationStatusBadge";
import BaseTable from "@/Components/Base/BaseTable/BaseTable";
import styles from "@/Styles/modules/Administration.module.css";
import { formatCompactNumber, formatDate, renderTooltip } from "@/Utils";

export interface AdministrationOwnersTableProps {
  data: AdministrationTaxOwnerSchema[];
  isLoading: boolean;
  onInspect: (owner: AdministrationTaxOwnerSchema) => void;
  onUpdate: (owner: AdministrationTaxOwnerSchema, forceRefresh: boolean) => void;
  onDelete: (owner: AdministrationTaxOwnerSchema) => void;
  isUpdating?: boolean;
  canForceRefresh?: boolean;
}

export function AdministrationOwnersTable({
  data,
  isLoading,
  onInspect,
  onUpdate,
  onDelete,
  isUpdating = false,
  canForceRefresh = false,
}: AdministrationOwnersTableProps) {
  const { t } = useTranslation();
  const [errorOwner, setErrorOwner] = useState<AdministrationTaxOwnerSchema | null>(null);

  const columns = useMemo<ColumnDef<AdministrationTaxOwnerSchema, unknown>[]>(
    () => {
      return [
      {
        id: "owner",
        header: t("Owner"),
        accessorKey: "name",
        cell: ({ row }) => {
          const item = row.original;
          return (
            <div className="d-flex align-items-center gap-2">
              {item.icon ? (
                <img
                  src={item.icon}
                  alt={item.name}
                  width={32}
                  height={32}
                  className="rounded-circle border border-secondary"
                />
              ) : (
                <div
                  className={`rounded-circle bg-secondary d-flex align-items-center justify-content-center text-light ${styles.avatarFallback}`}
                >
                  {item.name.charAt(0)}
                </div>
              )}
              <div className="d-flex flex-column">
                <span className="fw-semibold text-light">{item.name}</span>
                {item.ticker && (
                  <span className="text-muted small">[{item.ticker}]</span>
                )}
              </div>
            </div>
          );
        },
      },
      {
        id: "type",
        header: t("Type"),
        accessorKey: "owner_type",
        cell: ({ row }) => {
          const type = row.original.owner_type;
          return (
            <Badge bg={type === "corporation" ? "primary" : "info"}>
              {type === "corporation" ? t("Corporation") : t("Alliance")}
            </Badge>
          );
        },
      },
      {
        id: "status",
        header: t("Status"),
        accessorKey: "status",
        cell: ({ row }) => {
          const item = row.original;
          const hasError =
            Boolean(item.error_message) || item.status.toLowerCase() === "token_error";
          return (
            <AdministrationStatusBadge
              status={item.status}
              onClick={hasError ? () => setErrorOwner(item) : undefined}
              ariaLabel={
                hasError
                  ? t("Show error details for {{name}}", { name: item.name })
                  : undefined
              }
            />
          );
        },
      },
      {
        id: "tax_info",
        header: t("Tax Configuration"),
        accessorKey: "tax_amount",
        cell: ({ row }) => {
          const item = row.original;
          return (
            <div className="d-flex flex-column">
              <span className="fw-semibold text-light">
                {formatCompactNumber(item.tax_amount)} ISK
              </span>
              <span className="text-muted small">
                {t("Period: {{days}} days", { days: item.tax_period })}
              </span>
            </div>
          );
        },
      },
      {
        id: "open_invoices",
        header: t("Open Invoices"),
        accessorKey: "open_invoices",
        cell: ({ row }) => {
          const invoices = row.original.open_invoices;
          return invoices > 0 ? (
            <Badge bg="warning" text="dark">
              {invoices}
            </Badge>
          ) : (
            <span className="text-muted">0</span>
          );
        },
      },
      {
        id: "last_sync",
        header: t("Last Sync"),
        accessorKey: "last_sync",
        cell: ({ row }) => {
          const lastSync = row.original.last_sync;
          if (!lastSync) return <span className="text-muted">{t("Never")}</span>;
          const date = new Date(lastSync);
          return (
            <span className="text-muted small" title={date.toISOString()}>
              {formatDate(lastSync)}
            </span>
          );
        },
      },
      {
        id: "actions",
        header: () => <div className="text-end">{t("Actions")}</div>,
        cell: ({ row }) => {
          const item = row.original;
          return (
            <div className="d-flex align-items-center justify-content-end gap-2">
              {renderTooltip(
                t("Inspect"),
                <Button
                  variant="link"
                  size="sm"
                  onClick={() => onInspect(item)}
                  title={t("Inspect")}
                  className="d-inline-flex align-items-center gap-1 aa-btn aa-btn-primary"
                  data-testid={`inspect-btn-${item.owner_type}-${item.owner_id}`}
                >
                  <Eye size={13} />
                  <span>{t("Inspect")}</span>
                </Button>
              )}

              <Dropdown as={ButtonGroup} size="sm">
                {renderTooltip(
                  t("Update"),
                  <Button
                    variant="danger"
                    size="sm"
                    disabled={isUpdating}
                    onClick={() => onUpdate(item, false)}
                    title={t("Update")}
                    className="d-inline-flex align-items-center gap-1 aa-btn aa-btn-danger"
                    data-testid={`update-btn-${item.owner_type}-${item.owner_id}`}
                  >
                    {isUpdating ? (
                      <Spinner size="sm" animation="border" />
                    ) : (
                      <RefreshCw size={13} />
                    )}
                    <span>{t("Update")}</span>
                  </Button>
                )}
                {renderTooltip(
                  t("More update options"),
                  <Dropdown.Toggle
                    split
                    size="sm"
                    variant="danger"
                    aria-label={t("More update options")}
                    disabled={isUpdating}
                    id={`update-dropdown-${item.owner_id}`}
                    className="aa-btn aa-btn-danger"
                  />
                )}
                <Dropdown.Menu
                  align="end"
                  className={`shadow-lg ${styles.dropdownMenu}`}
                >
                  <Dropdown.Item onClick={() => onUpdate(item, false)}>
                    <RefreshCw size={14} className="me-2 text-primary" />
                    {t("Update (Normal)")}
                  </Dropdown.Item>
                  {canForceRefresh && (
                    <Dropdown.Item onClick={() => onUpdate(item, true)}>
                      <RefreshCw size={14} className="me-2 text-warning" />
                      {t("Force Refresh (Bypass cache)")}
                    </Dropdown.Item>
                  )}
                </Dropdown.Menu>
              </Dropdown>

              {renderTooltip(
                t("Delete"),
                <Button
                  variant="danger"
                  size="sm"
                  onClick={() => onDelete(item)}
                  title={t("Delete")}
                  className="d-inline-flex align-items-center gap-1 aa-btn aa-btn-danger"
                  data-testid={`delete-btn-${item.owner_type}-${item.owner_id}`}
                >
                  <Trash2 size={13} />
                  <span>{t("Delete")}</span>
                </Button>
              )}
            </div>
          );
        },
      },
    ];
  }, [t, onInspect, onUpdate, onDelete, isUpdating, canForceRefresh]);

  return (
    <>
      <BaseTable
        data={data}
        columns={columns}
        isFetching={isLoading}
        emptyText={t("No owners found.")}
      />
      <AdministrationErrorModal
        show={errorOwner !== null}
        onHide={() => setErrorOwner(null)}
        ownerName={errorOwner?.name ?? ""}
        status={errorOwner?.status ?? ""}
        errorMessage={errorOwner?.error_message}
      />
    </>
  );
}

export default AdministrationOwnersTable;
