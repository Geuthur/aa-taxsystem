// Third Party
import { formatCompactNumber, formatDate, renderTooltip, OwnerPortrait } from "aa-geuthur-react";
import type { BaseColumnDef } from "aa-geuthur-react";
import type { TFunction } from "i18next";
import { CheckCircle2, DollarSign, History, RotateCcw, ShieldCheck, ToggleLeft, ToggleRight, XCircle } from "lucide-react";
import { Badge, Button, ButtonGroup } from "react-bootstrap";

// AA TaxSystem
import type { components } from "@/Api/OpenApi";

export type AccountRow = components["schemas"]["PaymentSystemSchema"];

/** An account is unpaid when it owes tax: members of a tax-free group never do. */
export function isAccountUnpaid(account: AccountRow): boolean {
  return !account.has_paid && !account.is_tax_free;
}

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
}: AccountColumnsOptions): BaseColumnDef<AccountRow>[] {
  return [
    {
      id: "character",
      header: t("Character"),
      accessorFn: (row) => row.account?.character_name,
      cell: ({ row }) => {
        const openInvoices = row.original.open_invoices ?? 0;
        return (
          <div className="d-flex align-items-center gap-2">
            <OwnerPortrait
              src={row.original.account?.character_portrait}
              alt={row.original.account?.character_name}
              size="sm"
            />
            <span className="fw-semibold">{row.original.account?.character_name}</span>
            {openInvoices > 0 &&
              renderTooltip(
                t("{{count}} pending payment(s) to review/approve", {
                  count: openInvoices,
                }),
                <Button
                  variant="warning"
                  size="sm"
                  className="aa-pulse"
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
            {formatCompactNumber(val, "ISK")}
          </span>
        );
      },
    },
    {
      id: "has_paid",
      header: t("Paid"),
      accessorKey: "has_paid",
      cell: ({ getValue, row }) => {
        if (row.original.is_tax_free) {
          return (
            <Badge bg="secondary" className="d-inline-flex align-items-center gap-1">
              <ShieldCheck size={12} />
              {t("Tax-Free")}
            </Badge>
          );
        }
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
        return <span className="small text-muted">{formatDate(String(val), { dateStyle: "medium" })}</span>;
      },
    },
    {
      id: "actions",
      header: t("Actions"),
      cell: ({ row }) => (
        <ButtonGroup size="sm">
          {renderTooltip(
            t("Payment History & Activities"),
            <Button
              variant="info"
              aria-label={t("History")}
              onClick={() => onHistory(row.original)}
            >
              <History size={14} />
            </Button>,
          )}
          {renderTooltip(
            t("Add Custom Payment"),
            <Button
              variant="success"
              aria-label={t("Add Payment")}
              onClick={() => onAddPayment(row.original)}
            >
              <DollarSign size={14} />
            </Button>,
          )}
          {renderTooltip(
            t("Switch Account Status"),
            <Button
              variant="secondary"
              aria-label={t("Status")}
              onClick={() => onSwitchStatus(row.original)}
            >
              {row.original.status?.toLowerCase() === "active" ? (
                <ToggleRight size={14} className="text-success" />
              ) : (
                <ToggleLeft size={14} />
              )}
            </Button>,
          )}
          {onReset &&
            renderTooltip(
              t("Reset Account Balance & Due Date"),
              <Button
                variant="danger"
                aria-label={t("Reset")}
                onClick={() => onReset(row.original)}
              >
                <RotateCcw size={14} />
              </Button>,
            )}
        </ButtonGroup>
      ),
    },
  ];
}
