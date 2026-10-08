// React
import { useMemo } from "react";

// Third Party
import { type ColumnDef } from "@tanstack/react-table";
import { Users } from "lucide-react";
import { Badge, Button, Image } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// AA TaxSystem
import type { components } from "@/Api/OpenApi";
import { BaseModal, ModalSize } from "@/Components/Base/BaseModal";
import { BaseTable } from "@/Components/Base/BaseTable";

type AltCharacter = components["schemas"]["CharacterSchema"];

interface MemberAltsModalProps {
  mainCharacterName: string;
  mainCharacterPortrait?: string;
  alts: AltCharacter[];
  show: boolean;
  onClose: () => void;
}

export function MemberAltsModal({
  mainCharacterName,
  mainCharacterPortrait,
  alts,
  show,
  onClose,
}: MemberAltsModalProps) {
  const { t } = useTranslation();

  const columns = useMemo<ColumnDef<AltCharacter>[]>(
    () => [
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
    ],
    [t],
  );

  return (
    <BaseModal
      show={show}
      onHide={onClose}
      size={ModalSize.medium}
      title={
        <div className="d-flex align-items-center gap-2">
          {mainCharacterPortrait && (
            <Image
              src={mainCharacterPortrait}
              alt={mainCharacterName}
              roundedCircle
              width={28}
              height={28}
            />
          )}
          <Users size={18} className="text-info" />
          <span>
            {t("Alts of {{name}}", { name: mainCharacterName })}
          </span>
          <Badge bg="info" className="ms-1">
            {alts.length}
          </Badge>
        </div>
      }
      footer={
        <Button className="aa-btn aa-btn-sm aa-btn-secondary" onClick={onClose}>
          {t("Close")}
        </Button>
      }
    >
      <div className="mb-2">
        <BaseTable
          data={alts}
          columns={columns}
          isFetching={false}
          isError={false}
          emptyText={t("No alt characters found.")}
          variant="vowra-light"
        />
      </div>
    </BaseModal>
  );
}

export default MemberAltsModal;
