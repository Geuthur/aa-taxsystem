// Third Party
import { type ColumnDef } from "@tanstack/react-table";
import type { TFunction } from "i18next";
import { Badge, Image } from "react-bootstrap";

// AA TaxSystem
import type { components } from "@/Api/OpenApi";

export type AltCharacter = components["schemas"]["CharacterSchema"];

export interface AltColumnsOptions {
  t: TFunction;
}

export function getAltColumns({ t }: AltColumnsOptions): ColumnDef<AltCharacter>[] {
  return [
    {
      id: "character",
      header: t("Character"),
      accessorKey: "character_name",
      cell: ({ row }) => (
        <div className="d-flex align-items-center gap-2">
          {row.original.character_portrait && (
            <Image
              src={row.original.character_portrait}
              alt={row.original.character_name}
              roundedCircle
              width={32}
              height={32}
            />
          )}
          <span className="fw-semibold text-light">
            {row.original.character_name}
          </span>
        </div>
      ),
    },
    {
      id: "corporation",
      header: t("Corporation"),
      accessorKey: "corporation_name",
      cell: ({ row }) => {
        const corpName = row.original.corporation_name;
        const allianceName = row.original.alliance_name;
        if (!corpName && !allianceName) {
          return <span className="text-muted">—</span>;
        }
        return (
          <div className="d-flex align-items-center gap-1">
            {corpName && <Badge bg="secondary">{corpName}</Badge>}
            {allianceName && <span className="small text-muted">{allianceName}</span>}
          </div>
        );
      },
    },
  ];
}
