// React
import { useMemo } from "react";

// Third Party
import { Users } from "lucide-react";
import { Badge, Button, Image } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// AA TaxSystem
import type { components } from "@/Api/OpenApi";
import { BaseModal, ModalSize } from "@/Components/Base/BaseModal";
import { BaseTable } from "@/Components/Base/BaseTable";
import { getAltColumns } from "@/Components/Tables";

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

  const columns = useMemo(() => getAltColumns({ t }), [t]);

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
      bodyClassName="aa-panel"
      footer={
        <Button variant="secondary" onClick={onClose}>
          {t("Close")}
        </Button>
      }
    >
      <BaseTable
        variant="vowra-light"
        data={alts || []}
        columns={columns}
        emptyText={t("No alt characters recorded.")}
      />
    </BaseModal>
  );
}

export default MemberAltsModal;
