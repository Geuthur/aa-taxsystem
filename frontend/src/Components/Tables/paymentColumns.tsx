// React
import React from "react";

// Third Party
import { type ColumnDef } from "@tanstack/react-table";
import type { TFunction } from "i18next";
import { Badge } from "react-bootstrap";

// AA TaxSystem
import type { components } from "@/Api/OpenApi";
import { formatNumber } from "@/Utils";

export type PaymentRow = components["schemas"]["PaymentSchema"];
export type CorpPaymentRow = components["schemas"]["PaymentCorporationSchema"];
export type GenericPaymentRow = PaymentRow | CorpPaymentRow;

export interface PaymentColumnsOptions<T extends GenericPaymentRow> {
  t: TFunction;
  showCharacter?: boolean;
  showReviser?: boolean;
  renderActions?: (row: T) => React.ReactNode;
}

export function getPaymentColumns<T extends GenericPaymentRow>({
  t,
  showCharacter = false,
  showReviser = false,
  renderActions,
}: PaymentColumnsOptions<T>): ColumnDef<T>[] {
  const columns: ColumnDef<T>[] = [];

  if (showCharacter) {
    columns.push({
      id: "character",
      header: t("Character"),
      accessorFn: (row: T) =>
        "character" in row
          ? (row as CorpPaymentRow).character?.character_name
          : undefined,
      cell: ({ row }) => {
        const char =
          "character" in row.original
            ? (row.original as CorpPaymentRow).character
            : undefined;
        return (
          <div className="d-flex align-items-center gap-2">
            {char?.character_portrait && (
              <img
                src={char.character_portrait}
                alt={char.character_name}
                width={32}
                height={32}
                className="rounded-circle"
              />
            )}
            <span className="fw-semibold">{char?.character_name}</span>
          </div>
        );
      },
    });
  }

  columns.push(
    {
      id: "date",
      header: t("Date"),
      accessorKey: "date",
      cell: ({ getValue }) => (
        <span className="small text-muted">{String(getValue() || "—")}</span>
      ),
    },
    {
      id: "amount",
      header: t("Amount"),
      accessorKey: "amount",
      cell: ({ getValue }) => {
        const val = Number(getValue() || 0);
        return <span className="fw-mono text-light">{formatNumber(val)}</span>;
      },
    },
    {
      id: "division",
      header: t("Division"),
      accessorKey: "division_name",
      cell: ({ getValue }) => <span>{String(getValue() || "—")}</span>,
    },
    {
      id: "status",
      header: t("Status"),
      cell: ({ row }) => {
        const s = row.original.request_status;
        return (
          <Badge bg={s?.color || "secondary"}>
            {s?.status || t("Unknown")}
          </Badge>
        );
      },
    },
    {
      id: "reason",
      header: t("Reason"),
      accessorKey: "reason",
      cell: ({ getValue }) => <span>{String(getValue() || "—")}</span>,
    },
  );

  if (showReviser) {
    columns.push({
      id: "reviser",
      header: t("Reviser"),
      accessorKey: "reviser",
      cell: ({ getValue }) => (
        <span className="small text-muted">{String(getValue() || "—")}</span>
      ),
    });
  }

  if (renderActions) {
    columns.push({
      id: "actions",
      header: t("Actions"),
      cell: ({ row }) => renderActions(row.original),
    });
  }

  return columns;
}
