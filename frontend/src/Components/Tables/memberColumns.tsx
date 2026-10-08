// Third Party
import { type ColumnDef } from "@tanstack/react-table";
import type { TFunction } from "i18next";
import { History, Trash2, Users } from "lucide-react";
import { Badge, Button } from "react-bootstrap";

// AA TaxSystem
import type { components } from "@/Api/OpenApi";
import { renderTooltip } from "@/Utils";

export type MemberRow = components["schemas"]["MembersSchema"];

export interface MemberColumnsOptions {
  t: TFunction;
  onOpenAlts: (member: MemberRow) => void;
  onHistory: (member: MemberRow) => void;
  onDeleteMissing: (member: MemberRow) => void;
}

export function getMemberColumns({
  t,
  onOpenAlts,
  onHistory,
  onDeleteMissing,
}: MemberColumnsOptions): ColumnDef<MemberRow>[] {
  return [
    {
      id: "character",
      header: t("Character"),
      accessorFn: (row) => row.character?.character_name,
      cell: ({ row }) => {
        const openInvoices = row.original.open_invoices ?? 0;
        const alts = row.original.alts ?? [];
        return (
          <div className="d-flex align-items-center gap-2">
            {row.original.character?.character_portrait && (
              <img
                src={row.original.character.character_portrait}
                alt={row.original.character.character_name}
                width={32}
                height={32}
                className="rounded-circle"
              />
            )}
            <span className="fw-semibold">{row.original.character?.character_name}</span>
            {alts.length > 0 &&
              renderTooltip(
                t("Show {{count}} alt character(s)", {
                  count: alts.length,
                }),
                <Button
                  className="aa-btn aa-btn-sm aa-btn-secondary d-inline-flex align-items-center gap-1 py-0 px-2"
                  style={{ fontSize: "0.75rem", height: "24px" }}
                  onClick={(e) => {
                    e.stopPropagation();
                    onOpenAlts(row.original);
                  }}
                >
                  <Users size={12} />
                  <span>
                    {alts.length} {t("Alts")}
                  </span>
                </Button>,
              )}
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
      cell: ({ getValue }) => (
        <Badge bg="secondary">{String(getValue() || "")}</Badge>
      ),
    },
    {
      id: "missing",
      header: t("Missing"),
      accessorKey: "is_missing",
      cell: ({ getValue }) => {
        const isMissing = Boolean(getValue());
        return isMissing ? (
          <Badge bg="danger">{t("Missing")}</Badge>
        ) : (
          <Badge bg="success">{t("Active")}</Badge>
        );
      },
    },
    {
      id: "joined",
      header: t("Joined"),
      accessorKey: "joined",
      cell: ({ getValue }) => {
        const val = getValue();
        if (!val) return "—";
        return new Date(String(val)).toLocaleDateString();
      },
    },
    {
      id: "actions",
      header: t("Actions"),
      cell: ({ row }) => (
        <div className="d-flex align-items-center gap-1">
          {row.original.character?.character_id &&
            renderTooltip(
              t("Payment History & Activities"),
              <Button
                className="aa-btn aa-btn-sm aa-btn-info"
                onClick={() => onHistory(row.original)}
              >
                <History size={12} />
                {t("History")}
              </Button>,
            )}
          {row.original.is_missing && row.original.character?.character_id && (
            <Button
              className="aa-btn aa-btn-sm aa-btn-danger"
              onClick={() => onDeleteMissing(row.original)}
            >
              <Trash2 size={12} />
              {t("Delete")}
            </Button>
          )}
        </div>
      ),
    },
  ];
}
