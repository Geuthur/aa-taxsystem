// React
import { useMemo, useState } from "react";

// Third Party
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { type ColumnDef } from "@tanstack/react-table";
import { AlertCircle, History, Search, Trash2, Users } from "lucide-react";
import { Badge, Button, Form, InputGroup, Spinner } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// AA TaxSystem
import { deleteMember, loadMembers } from "@/Api/ApiCalls";
import type { components } from "@/Api/OpenApi";
import { queryKeys } from "@/Api/query";
import { BaseModal, ModalSize } from "@/Components/Base/BaseModal";
import { BaseTable } from "@/Components/Base/BaseTable";
import { useTableSearchState } from "@/Hooks/useTaxsystemState";
import { MemberAltsModal } from "@/Pages/Manage/Modals/MemberAltsModal";
import { MemberPaymentsModal } from "@/Pages/Manage/Modals/MemberPaymentsModal";
import { renderTooltip } from "@/Utils";

interface MembersTabProps {
  ownerId: number;
}

type MemberRow = components["schemas"]["MembersSchema"];

export function MembersTab({ ownerId }: MembersTabProps) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [search, setSearch] = useTableSearchState("memberSearch");
  const [memberToDelete, setMemberToDelete] = useState<MemberRow | null>(null);
  const [altsMember, setAltsMember] = useState<MemberRow | null>(null);
  const [historyMember, setHistoryMember] = useState<{
    characterId: number;
    characterName: string;
    characterPortrait?: string;
  } | null>(null);

  const { data: members, isLoading, isError } = useQuery({
    queryKey: queryKeys.Members(ownerId),
    queryFn: () => loadMembers(ownerId),
  });

  const deleteMutation = useMutation({
    mutationFn: (memberPk: number) => deleteMember(ownerId, memberPk),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.Members(ownerId) });
      setMemberToDelete(null);
    },
  });

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

  const columns = useMemo<ColumnDef<MemberRow>[]>(
    () => [
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
                      setAltsMember(row.original);
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
                      if (row.original.character?.character_id) {
                        setHistoryMember({
                          characterId: row.original.character.character_id,
                          characterName: row.original.character?.character_name || "",
                          characterPortrait: row.original.character?.character_portrait,
                        });
                      }
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
                  onClick={() => {
                    setHistoryMember({
                      characterId: row.original.character!.character_id!,
                      characterName: row.original.character?.character_name || "",
                      characterPortrait: row.original.character?.character_portrait,
                    });
                  }}
                >
                  <History size={12} />
                  {t("History")}
                </Button>,
              )}
            {row.original.is_missing && row.original.character?.character_id && (
              <Button
                className="aa-btn aa-btn-sm aa-btn-danger"
                onClick={() => setMemberToDelete(row.original)}
              >
                <Trash2 size={12} />
                {t("Delete")}
              </Button>
            )}
          </div>
        ),
      },
    ],
    [t],
  );

  return (
    <div className="mt-3">
      <div className="d-flex justify-content-between align-items-center mb-3">
        <InputGroup style={{ maxWidth: 360 }}>
          <InputGroup.Text className="bg-dark border-secondary text-secondary">
            <Search size={16} />
          </InputGroup.Text>
          <Form.Control
            type="text"
            placeholder={t("Filter members by name...")}
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="bg-dark text-light border-secondary"
          />
        </InputGroup>
      </div>

      <BaseTable
        data={filteredMembers}
        columns={columns}
        isFetching={isLoading}
        isError={isError}
        emptyText={t("No corporation members found.")}
        variant="vowra-light"
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
                disabled={deleteMutation.isPending}
                onClick={() => {
                  if (memberToDelete.character?.character_id) {
                    deleteMutation.mutate(memberToDelete.character.character_id);
                  }
                }}
              >
                {deleteMutation.isPending && <Spinner size="sm" animation="border" className="me-1" />}
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
