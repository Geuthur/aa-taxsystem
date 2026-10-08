// React
import { useMemo, useState } from "react";

// Third Party
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { type ColumnDef } from "@tanstack/react-table";
import { Plus, Trash2, Users2 } from "lucide-react";
import { Badge, Button, Card, Form, Spinner } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// AA TaxSystem
import {
  createGroup,
  deleteGroup,
  loadAvailableGroups,
  loadGroups,
} from "@/Api/ApiCalls";
import type { components } from "@/Api/OpenApi";
import { queryKeys } from "@/Api/query";
import { BaseModal, ModalSize } from "@/Components/Base/BaseModal";
import { BaseTable } from "@/Components/Base/BaseTable";

interface GroupsTabProps {
  ownerId: number;
}

type GroupManagementRow = components["schemas"]["GroupManagementSchema"];

export function GroupsTab({ ownerId }: GroupsTabProps) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();

  // Create Group Modal State
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [newGroupName, setNewGroupName] = useState("");
  const [selectedAuthGroupIds, setSelectedAuthGroupIds] = useState<number[]>([]);
  const [authGroupSearch, setAuthGroupSearch] = useState("");

  // Delete Group Modal State
  const [groupToDelete, setGroupToDelete] = useState<GroupManagementRow | null>(null);
  const [deleteComment, setDeleteComment] = useState("");

  const { data: groups, isLoading, isError } = useQuery({
    queryKey: queryKeys.Groups(ownerId),
    queryFn: () => loadGroups(ownerId),
  });

  const { data: availableGroups, isLoading: availableLoading } = useQuery({
    queryKey: queryKeys.AvailableGroups(ownerId),
    queryFn: () => loadAvailableGroups(ownerId),
    enabled: showCreateModal,
  });

  const createMutation = useMutation({
    mutationFn: () =>
      createGroup(ownerId, {
        name: newGroupName.trim(),
        group_ids: selectedAuthGroupIds,
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.Groups(ownerId) });
      setShowCreateModal(false);
      setNewGroupName("");
      setSelectedAuthGroupIds([]);
      setAuthGroupSearch("");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: ({ groupPk, comment }: { groupPk: number; comment: string }) =>
      deleteGroup(ownerId, groupPk, comment),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.Groups(ownerId) });
      setGroupToDelete(null);
      setDeleteComment("");
    },
  });

  const toggleAuthGroup = (groupId: number) => {
    setSelectedAuthGroupIds((prev) =>
      prev.includes(groupId) ? prev.filter((id) => id !== groupId) : [...prev, groupId],
    );
  };

  const filteredAvailableGroups = useMemo(() => {
    if (!availableGroups) return [];
    if (!authGroupSearch.trim()) return availableGroups;
    const q = authGroupSearch.toLowerCase();
    return availableGroups.filter((g) => g.name.toLowerCase().includes(q));
  }, [availableGroups, authGroupSearch]);

  const columns = useMemo<ColumnDef<GroupManagementRow>[]>(
    () => [
      {
        id: "name",
        header: t("Name"),
        accessorKey: "name",
        cell: ({ getValue }) => <span className="fw-semibold">{String(getValue() || "")}</span>,
      },
      {
        id: "groups",
        header: t("Assigned Groups"),
        cell: ({ row }) => (
          <div className="d-flex flex-wrap gap-1">
            {row.original.groups?.map((g) => (
              <Badge key={g.id} bg="primary">
                {g.name}
              </Badge>
            )) || <span className="text-muted">—</span>}
          </div>
        ),
      },
      {
        id: "actions",
        header: t("Actions"),
        cell: ({ row }) =>
          row.original.id ? (
            <Button
              className="aa-btn aa-btn-sm aa-btn-danger"
              onClick={() => {
                setGroupToDelete(row.original);
                setDeleteComment(t("Deleted via Tax System"));
              }}
            >
              <Trash2 size={12} />
              {t("Delete")}
            </Button>
          ) : null,
      },
    ],
    [t],
  );

  return (
    <div className="mt-3">
      <Card className="bg-dark border-secondary">
        <Card.Header className="d-flex align-items-center justify-content-between border-secondary">
          <h5 className="mb-0 d-flex align-items-center gap-2">
            <Users2 size={18} className="text-primary" />
            {t("Tax Groups")}
          </h5>
          <Button
            className="aa-btn aa-btn-sm aa-btn-primary"
            onClick={() => setShowCreateModal(true)}
          >
            <Plus size={14} />
            {t("Add Tax-Free Group")}
          </Button>
        </Card.Header>
        <Card.Body>
          <BaseTable
            data={groups || []}
            columns={columns}
            isFetching={isLoading}
            isError={isError}
            emptyText={t("No tax groups assigned.")}
          />
        </Card.Body>
      </Card>

      {/* Add Tax-Free Group Modal */}
      {showCreateModal && (
        <BaseModal
          show={showCreateModal}
          onHide={() => setShowCreateModal(false)}
          size={ModalSize.medium}
          title={
            <div className="h5 text-primary d-flex align-items-center gap-2 mb-0">
              <Users2 size={18} />
              {t("Add Tax-Free Group")}
            </div>
          }
          footer={
            <>
              <Button
                variant="secondary"
                onClick={() => setShowCreateModal(false)}
              >
                {t("Cancel")}
              </Button>
              <Button
                variant="primary"
                disabled={!newGroupName.trim() || createMutation.isPending}
                onClick={() => createMutation.mutate()}
              >
                {createMutation.isPending && <Spinner size="sm" animation="border" className="me-1" />}
                {t("Create")}
              </Button>
            </>
          }
        >
          <Form.Group className="mb-3">
            <Form.Label>{t("Group Name")}</Form.Label>
            <Form.Control
              type="text"
              placeholder={t("e.g. Leadership, Logistics")}
              value={newGroupName}
              onChange={(e) => setNewGroupName(e.target.value)}
              className="bg-dark text-light border-secondary"
              autoFocus
            />
          </Form.Group>

          <Form.Group className="mb-3">
            <Form.Label>{t("Select Auth Groups")}</Form.Label>
            <Form.Control
              type="text"
              placeholder={t("Search groups...")}
              value={authGroupSearch}
              onChange={(e) => setAuthGroupSearch(e.target.value)}
              size="sm"
              className="bg-dark text-light border-secondary mb-2"
            />
            <div
              className="p-2 aa-panel-light border border-secondary rounded overflow-auto"
              style={{ maxHeight: "200px" }}
            >
              {availableLoading ? (
                <div className="text-center py-3">
                  <Spinner size="sm" animation="border" className="text-primary" />
                </div>
              ) : filteredAvailableGroups.length === 0 ? (
                <div className="text-muted small text-center py-2">
                  {t("No auth groups found.")}
                </div>
              ) : (
                filteredAvailableGroups.map((g) => {
                  const isChecked = selectedAuthGroupIds.includes(g.id);
                  return (
                    <Form.Check
                      key={g.id}
                      type="checkbox"
                      id={`auth-group-${g.id}`}
                      label={g.name}
                      checked={isChecked}
                      onChange={() => toggleAuthGroup(g.id)}
                      className="mb-1"
                    />
                  );
                })
              )}
            </div>
            <Form.Text className="text-muted">
              {t(
                "Members belonging to any selected group will be exempt from taxes.",
              )}
            </Form.Text>
          </Form.Group>
        </BaseModal>
      )}

      {/* Delete Group Confirmation Modal */}
      {groupToDelete && (
        <BaseModal
          show={!!groupToDelete}
          onHide={() => setGroupToDelete(null)}
          size={ModalSize.medium}
          title={
            <div className="h5 text-danger d-flex align-items-center gap-2 mb-0">
              <Trash2 size={18} />
              {t("Delete Tax-Free Group")}
            </div>
          }
          footer={
            <>
              <Button
                variant="secondary"
                onClick={() => setGroupToDelete(null)}
              >
                {t("Cancel")}
              </Button>
              <Button
                variant="danger"
                disabled={deleteMutation.isPending}
                onClick={() => {
                  if (groupToDelete.id) {
                    deleteMutation.mutate({
                      groupPk: groupToDelete.id,
                      comment: deleteComment.trim() || t("Deleted via Tax System"),
                    });
                  }
                }}
              >
                {deleteMutation.isPending && <Spinner size="sm" animation="border" className="me-1" />}
                {t("Confirm Delete")}
              </Button>
            </>
          }
        >
          <p>
            {t("Are you sure you want to delete:")}{" "}
            <strong>{groupToDelete.name}</strong>?
          </p>
          <Form.Group className="mb-3">
            <Form.Label>{t("Reason / Comment")}</Form.Label>
            <Form.Control
              as="textarea"
              rows={2}
              value={deleteComment}
              onChange={(e) => setDeleteComment(e.target.value)}
              placeholder={t("Reason for deletion...")}
              className="bg-dark text-light border-secondary"
            />
          </Form.Group>
        </BaseModal>
      )}
    </div>
  );
}

export default GroupsTab;
