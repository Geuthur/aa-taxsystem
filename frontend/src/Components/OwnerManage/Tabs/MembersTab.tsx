// React
import { useMemo, useState } from "react";

// Third Party
import { AlertCircle } from "lucide-react";
import { Button, Spinner } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// AA TaxSystem
import type { components } from "@/Api/OpenApi";
import { BaseModal, ModalSize } from "@/Components/Base/BaseModal";
import { BaseTable } from "@/Components/Base/BaseTable";
import { SearchInput } from "@/Components/Base/SearchInput";
import { useMemberActions, useMembers } from "@/Components/OwnerManage/Hooks";
import { MemberAltsModal } from "@/Components/OwnerManage/Modals/MemberAltsModal";
import { MemberPaymentsModal } from "@/Components/OwnerManage/Modals/MemberPaymentsModal";
import { getMemberColumns } from "@/Components/Tables";
import { useTableSearchState } from "@/Hooks/useTaxsystemState";

interface MembersTabProps {
  ownerId: number;
}

type MemberRow = components["schemas"]["MembersSchema"];

export function MembersTab({ ownerId }: MembersTabProps) {
  const { t } = useTranslation();
  const [search, setSearch] = useTableSearchState("memberSearch");
  const [memberToDelete, setMemberToDelete] = useState<MemberRow | null>(null);
  const [altsMember, setAltsMember] = useState<MemberRow | null>(null);
  const [historyMember, setHistoryMember] = useState<{
    characterId: number;
    characterName: string;
    characterPortrait?: string;
  } | null>(null);

  const { data: members, isLoading, isError } = useMembers(ownerId);
  const memberActions = useMemberActions(ownerId, () => setMemberToDelete(null));

  const filteredMembers = useMemo(() => {
    if (!members) return [];
    const list = members.filter(
      (m) =>
        !m.is_alt &&
        m.status?.toLowerCase() !== "is alt" &&
        m.status?.toLowerCase() !== "is_alt",
    );
    if (!search) return list;
    const q = search.toLowerCase();
    return list.filter((m) =>
      m.character?.character_name?.toLowerCase().includes(q),
    );
  }, [members, search]);

  const columns = useMemo(
    () =>
      getMemberColumns({
        t,
        onOpenAlts: (member) => setAltsMember(member),
        onHistory: (member) => {
          if (member.character?.character_id) {
            setHistoryMember({
              characterId: member.character.character_id,
              characterName: member.character.character_name || "",
              characterPortrait: member.character.character_portrait,
            });
          }
        },
        onDeleteMissing: (member) => setMemberToDelete(member),
      }),
    [t],
  );

  return (
    <div className="mt-3">
      <div className="d-flex justify-content-between align-items-center mb-3">
        <SearchInput
            value={search}
            onChange={setSearch}
            placeholder={t("Filter members by name…")}
          />
      </div>

      <BaseTable
        data={filteredMembers}
        columns={columns}
        isFetching={isLoading}
        isError={isError}
        emptyText={t("No corporation members found.")}
        variant="light"
      />

      {/* Delete Member Confirmation Modal */}
      {memberToDelete && (
        <BaseModal
          show={!!memberToDelete}
          onHide={() => setMemberToDelete(null)}
          size={ModalSize.medium}
          title={
            <div className="h5 text-danger d-flex align-items-center gap-2 mb-0">
              <AlertCircle size={18} />
              {t("Delete Missing Member")}
            </div>
          }
          footer={
            <>
              <Button
                variant="secondary"
                onClick={() => setMemberToDelete(null)}
              >
                {t("Cancel")}
              </Button>
              <Button
                variant="danger"
                disabled={memberActions.isRemoving}
                onClick={() => {
                  if (memberToDelete.character?.character_id) {
                    memberActions.remove(memberToDelete.character.character_id);
                  }
                }}
              >
                {memberActions.isRemoving && <Spinner size="sm" animation="border" className="me-1" />}
                {t("Confirm Delete")}
              </Button>
            </>
          }
        >
          <p className="mb-0">
            {t(
              "Are you sure you want to remove the missing member records for:",
            )}{" "}
            <strong>{memberToDelete.character?.character_name}</strong>?
          </p>
        </BaseModal>
      )}

      {historyMember && (
        <MemberPaymentsModal
          ownerId={ownerId}
          characterId={historyMember.characterId}
          characterName={historyMember.characterName}
          characterPortrait={historyMember.characterPortrait}
          show
          onClose={() => setHistoryMember(null)}
        />
      )}

      {altsMember && (
        <MemberAltsModal
          mainCharacterName={altsMember.character?.character_name || ""}
          mainCharacterPortrait={altsMember.character?.character_portrait}
          alts={altsMember.alts || []}
          show={!!altsMember}
          onClose={() => setAltsMember(null)}
        />
      )}
    </div>
  );
}

export default MembersTab;
