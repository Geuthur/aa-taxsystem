// Third Party
import { type ColumnDef } from "@tanstack/react-table";
import type { TFunction } from "i18next";
import { CheckCircle2, DollarSign, History, RotateCcw, ToggleLeft, ToggleRight, XCircle } from "lucide-react";
import { Badge, Button } from "react-bootstrap";

// AA TaxSystem
import type { components } from "@/Api/OpenApi";
import { formatNumber, renderTooltip } from "@/Utils";

export type AccountRow = components["schemas"]["PaymentSystemSchema"];

export interface AccountColumnsOptions {
  t: TFunction;
  onHistory: (account: AccountRow) => void;
  onAddPayment: (account: AccountRow) => void;
  onSwitchStatus: (account: AccountRow) => void;
  onReset?: (account: AccountRow) => void;
}

export function getAccountColumns({
  t,
  onHistory,
  onAddPayment,
  onSwitchStatus,
  onReset,
}: AccountColumnsOptions): ColumnDef<AccountRow>[] {
  return [
    {
      id: "character",
      header: t("Character"),
      accessorFn: (row) => row.account?.character_name,
      cell: ({ row }) => {
        const openInvoices = row.original.open_invoices ?? 0;
        return (
          <div className="d-flex align-items-center gap-2">
            {row.original.account?.character_portrait && (
              <img
                src={row.original.account.character_portrait}
                alt={row.original.account.character_name}
                width={32}
                height={32}
                className="rounded-circle"
              />
            )}
            <span className="fw-semibold">{row.original.account?.character_name}</span>
            {openInvoices > 0 &&
              renderTooltip(
                t("{{count}} pending payment(s) to review/approve", {
                  count: openInvoices,
                }),
                <Button
                  className="aa-btn aa-btn-sm aa-btn-warning aa-btn-pulse"
                  onClick={(e) => {
                    e.stopPropagation();
                    onHistory(row.original);
                  }}
                >
                  <span className="aa-pending-dot-container">
                    <span className="aa-pending-dot-ping" />
                    <span className="aa-pending-dot-core" />
                  </span>
                  <span>
                    {openInvoices} {t("Pending")}
                  </span>
                </Button>,
              )}
          </div>
        );
      },
    },
    {
      id: "status",
      header: t("Status"),
      accessorKey: "status",
      cell: ({ getValue }) => {
        const val = String(getValue() || "");
        const isOk = val.toLowerCase().includes("ok") || val.toLowerCase().includes("active");
        return (
          <Badge bg={isOk ? "success" : "warning"} className="text-uppercase">
            {val}
          </Badge>
        );
      },
    },
    {
      id: "deposit",
      header: t("Deposit"),
      accessorKey: "deposit",
      cell: ({ getValue }) => {
        const val = Number(getValue() || 0);
        return (
          <span className={`fw-mono ${val < 0 ? "text-danger" : "text-light"}`}>
            {formatNumber(val)}
          </span>
        );
      },
    },
    {
      id: "has_paid",
      header: t("Paid"),
      accessorKey: "has_paid",
      cell: ({ getValue }) => {
        const isPaid = Boolean(getValue());
        return isPaid ? (
          <Badge bg="success" className="d-inline-flex align-items-center gap-1">
            <CheckCircle2 size={12} />
            {t("Paid")}
          </Badge>
        ) : (
          <Badge bg="danger" className="d-inline-flex align-items-center gap-1">
            <XCircle size={12} />
            {t("Unpaid")}
          </Badge>
        );
      },
    },
    {
      id: "next_due",
      header: t("Next Due"),
      accessorKey: "next_due",
      cell: ({ getValue }) => {
        const val = getValue();
        if (!val) return <span className="text-muted">—</span>;
        return <span className="small text-muted">{new Date(String(val)).toLocaleDateString()}</span>;
      },
    },
    {
      id: "actions",
      header: t("Actions"),
      cell: ({ row }) => (
        <div className="d-flex align-items-center gap-1">
          {renderTooltip(
            t("Payment History & Activities"),
            <Button
              className="aa-btn aa-btn-sm aa-btn-info"
              onClick={() => onHistory(row.original)}
            >
              <History size={12} />
              {t("History")}
            </Button>,
          )}
          {renderTooltip(
            t("Add Custom Payment"),
            <Button
              className="aa-btn aa-btn-sm aa-btn-success"
              onClick={() => onAddPayment(row.original)}
            >
              <DollarSign size={12} />
              {t("Add Payment")}
            </Button>,
          )}
          {renderTooltip(
            t("Switch Account Status"),
            <Button
              className="aa-btn aa-btn-sm aa-btn-secondary"
              onClick={() => onSwitchStatus(row.original)}
            >
              {row.original.status?.toLowerCase() === "active" ? (
                <ToggleRight size={12} className="text-success" />
              ) : (
                <ToggleLeft size={12} />
              )}
              {t("Status")}
            </Button>,
          )}
          {onReset &&
            renderTooltip(
              t("Reset Account Balance & Due Date"),
              <Button
                className="aa-btn aa-btn-sm aa-btn-danger"
                onClick={() => onReset(row.original)}
              >
                <RotateCcw size={12} />
                {t("Reset")}
              </Button>,
            )}
        </div>
      ),
    },
  ];
}
