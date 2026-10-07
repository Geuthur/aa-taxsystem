// React
import { useMemo, useState } from "react";

// Third Party
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { type ColumnDef } from "@tanstack/react-table";
import { Filter, Layers, Plus, Trash2 } from "lucide-react";
import { Badge, Button, Card, Col, Form, Row, Spinner } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// AA TaxSystem
import {
  createFilter,
  createFilterSet,
  deleteFilter,
  deleteFilterSet,
  loadFilters,
  loadFilterSets,
} from "@/Api/ApiCalls";
import type { components } from "@/Api/OpenApi";
import { queryKeys } from "@/Api/query";
import { BaseModal, ModalSize } from "@/Components/Base/BaseModal";
import { BaseTable } from "@/Components/Base/BaseTable";

interface FiltersTabProps {
  ownerId: number;
}

type FilterSetRow = components["schemas"]["FilterSetModelSchema"];
type FilterRow = components["schemas"]["FilterModelSchema"];

export function FiltersTab({ ownerId }: FiltersTabProps) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();

  const [selectedFilterSetId, setSelectedFilterSetId] = useState<number | null>(null);
  const [filterSetToDelete, setFilterSetToDelete] = useState<number | null>(null);
  const [filterToDelete, setFilterToDelete] = useState<number | null>(null);

  // Create Filter Set Modal State
  const [showCreateSetModal, setShowCreateSetModal] = useState(false);
  const [newSetName, setNewSetName] = useState("");
  const [newSetDescription, setNewSetDescription] = useState("");

  // Create Filter Modal State
  const [showCreateFilterModal, setShowCreateFilterModal] = useState(false);
  const [newFilterSetId, setNewFilterSetId] = useState<number | null>(null);
  const [newFilterType, setNewFilterType] = useState<"reason" | "amount">("reason");
  const [newMatchType, setNewMatchType] = useState<"exact" | "contains">("exact");
  const [newFilterValue, setNewFilterValue] = useState("");

  const { data: filterSets, isLoading: setsLoading } = useQuery({
    queryKey: queryKeys.FilterSets(ownerId),
    queryFn: () => loadFilterSets(ownerId),
  });

  const activeSetId = selectedFilterSetId ?? filterSets?.[0]?.id ?? null;

  const { data: filters, isLoading: filtersLoading } = useQuery({
    queryKey: queryKeys.Filters(ownerId, activeSetId ?? undefined),
    queryFn: () => (activeSetId ? loadFilters(ownerId, activeSetId) : Promise.resolve([])),
    enabled: activeSetId !== null,
  });

  const createSetMutation = useMutation({
    mutationFn: () =>
      createFilterSet(ownerId, {
        name: newSetName.trim(),
        description: newSetDescription.trim(),
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.FilterSets(ownerId) });
      setShowCreateSetModal(false);
      setNewSetName("");
      setNewSetDescription("");
    },
  });

  const createFilterMutation = useMutation({
    mutationFn: () => {
      const targetSetId = newFilterSetId ?? activeSetId;
      if (!targetSetId) throw new Error("No filter set selected");
      return createFilter(ownerId, {
        filter_set_id: targetSetId,
        filter_type: newFilterType,
        match_type: newMatchType,
        value: newFilterValue.trim(),
      });
    },
    onSuccess: () => {
      const targetSetId = newFilterSetId ?? activeSetId;
      queryClient.invalidateQueries({ queryKey: queryKeys.Filters(ownerId, targetSetId ?? undefined) });
      setShowCreateFilterModal(false);
      setNewFilterValue("");
    },
  });

  const deleteSetMutation = useMutation({
    mutationFn: (filtersetPk: number) => deleteFilterSet(ownerId, filtersetPk),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.FilterSets(ownerId) });
      setFilterSetToDelete(null);
    },
  });

  const deleteFilterMutation = useMutation({
    mutationFn: (filterPk: number) => deleteFilter(ownerId, filterPk),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.Filters(ownerId, activeSetId ?? undefined) });
      setFilterToDelete(null);
    },
  });

  const setColumns = useMemo<ColumnDef<FilterSetRow>[]>(
    () => [
      {
        id: "name",
        header: t("Name", "Name"),
        accessorKey: "name",
        cell: ({ row }) => (
          <Button
            variant="link"
            className={`p-0 fw-semibold text-decoration-none ${row.original.id === activeSetId ? "text-primary" : "text-light"}`}
            onClick={() => row.original.id && setSelectedFilterSetId(row.original.id)}
          >
            {row.original.name}
          </Button>
        ),
      },
      {
        id: "description",
        header: t("Description", "Description"),
        accessorKey: "description",
      },
      {
        id: "enabled",
        header: t("Status", "Status"),
        accessorKey: "enabled",
        cell: ({ getValue }) =>
          getValue() ? (
            <Badge bg="success">{t("Enabled", "Enabled")}</Badge>
          ) : (
            <Badge bg="secondary">{t("Disabled", "Disabled")}</Badge>
          ),
      },
      {
        id: "actions",
        header: t("Actions", "Actions"),
        cell: ({ row }) =>
          row.original.id ? (
            <Button
              variant="outline-danger"
              size="sm"
              onClick={() => setFilterSetToDelete(row.original.id!)}
            >
              <Trash2 size={12} className="me-1" />
              {t("Delete", "Delete")}
            </Button>
          ) : null,
      },
    ],
    [t, activeSetId],
  );

  const filterColumns = useMemo<ColumnDef<FilterRow>[]>(
    () => [
      {
        id: "filter_set",
        header: t("Filter Set", "Filter Set"),
        accessorFn: (row) => row.filter_set?.name,
      },
      {
        id: "filter_type",
        header: t("Type", "Type"),
        accessorKey: "filter_type",
      },
      {
        id: "match_type",
        header: t("Match", "Match"),
        accessorKey: "match_type",
      },
      {
        id: "value",
        header: t("Value", "Value"),
        cell: ({ row }) => {
          const v = row.original.value;
          if (typeof v === "object" && v !== null && "display" in v) {
            return String(v.display);
          }
          return String(v ?? "");
        },
      },
      {
        id: "actions",
        header: t("Actions", "Actions"),
        cell: ({ row }) =>
          row.original.id ? (
            <Button
              variant="outline-danger"
              size="sm"
              onClick={() => setFilterToDelete(row.original.id!)}
            >
              <Trash2 size={12} className="me-1" />
              {t("Delete", "Delete")}
            </Button>
          ) : null,
      },
    ],
    [t],
  );

  return (
    <div className="mt-3">
      <Row className="g-4">
        <Col xs={12}>
          <Card className="bg-dark border-secondary">
            <Card.Header className="d-flex align-items-center justify-content-between border-secondary">
              <h5 className="mb-0 d-flex align-items-center gap-2">
                <Layers size={18} className="text-primary" />
                {t("Filter Sets", "Filter Sets")}
              </h5>
              <Button
                variant="outline-primary"
                size="sm"
                onClick={() => setShowCreateSetModal(true)}
              >
                <Plus size={14} className="me-1" />
                {t("Add Filter Set", "Add Filter Set")}
              </Button>
            </Card.Header>
            <Card.Body className="p-0">
              <BaseTable
                data={filterSets || []}
                columns={setColumns}
                isFetching={setsLoading}
                emptyText={t("No filter sets defined.", "No filter sets defined.")}
              />
            </Card.Body>
          </Card>
        </Col>

        <Col xs={12}>
          <Card className="bg-dark border-secondary">
            <Card.Header className="d-flex align-items-center justify-content-between border-secondary">
              <h5 className="mb-0 d-flex align-items-center gap-2">
                <Filter size={18} className="text-info" />
                {t("Active Filters", "Active Filters")}
              </h5>
              <Button
                variant="outline-info"
                size="sm"
                disabled={!filterSets || filterSets.length === 0}
                onClick={() => {
                  setNewFilterSetId(activeSetId);
                  setShowCreateFilterModal(true);
                }}
              >
                <Plus size={14} className="me-1" />
                {t("Add Filter", "Add Filter")}
              </Button>
            </Card.Header>
            <Card.Body className="p-0">
              <BaseTable
                data={filters || []}
                columns={filterColumns}
                isFetching={filtersLoading}
                emptyText={t("No active filters found.", "No active filters found.")}
              />
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Create Filter Set Modal */}
      {showCreateSetModal && (
        <BaseModal
          show={showCreateSetModal}
          onHide={() => setShowCreateSetModal(false)}
          size={ModalSize.medium}
          title={
            <div className="h5 text-primary d-flex align-items-center gap-2 mb-0">
              <Layers size={18} />
              {t("Add Filter Set", "Add Filter Set")}
            </div>
          }
          footer={
            <>
              <Button variant="secondary" onClick={() => setShowCreateSetModal(false)}>
                {t("Cancel", "Cancel")}
              </Button>
              <Button
                variant="primary"
                disabled={!newSetName.trim() || createSetMutation.isPending}
                onClick={() => createSetMutation.mutate()}
              >
                {createSetMutation.isPending && <Spinner size="sm" animation="border" className="me-1" />}
                {t("Create", "Create")}
              </Button>
            </>
          }
        >
          <Form.Group className="mb-3">
            <Form.Label>{t("Name", "Name")}</Form.Label>
            <Form.Control
              type="text"
              value={newSetName}
              onChange={(e) => setNewSetName(e.target.value)}
              placeholder={t("e.g. Corp Tax Exemption", "e.g. Corp Tax Exemption")}
              className="bg-dark text-light border-secondary"
              autoFocus
            />
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>{t("Description", "Description")}</Form.Label>
            <Form.Control
              type="text"
              value={newSetDescription}
              onChange={(e) => setNewSetDescription(e.target.value)}
              placeholder={t("Optional description", "Optional description")}
              className="bg-dark text-light border-secondary"
            />
          </Form.Group>
        </BaseModal>
      )}

      {/* Create Filter Modal */}
      {showCreateFilterModal && (
        <BaseModal
          show={showCreateFilterModal}
          onHide={() => setShowCreateFilterModal(false)}
          size={ModalSize.medium}
          title={
            <div className="h5 text-info d-flex align-items-center gap-2 mb-0">
              <Filter size={18} />
              {t("Add Filter", "Add Filter")}
            </div>
          }
          footer={
            <>
              <Button variant="secondary" onClick={() => setShowCreateFilterModal(false)}>
                {t("Cancel", "Cancel")}
              </Button>
              <Button
                variant="info"
                disabled={!newFilterValue.trim() || createFilterMutation.isPending}
                onClick={() => createFilterMutation.mutate()}
              >
                {createFilterMutation.isPending && <Spinner size="sm" animation="border" className="me-1" />}
                {t("Create", "Create")}
              </Button>
            </>
          }
        >
          <Form.Group className="mb-3">
            <Form.Label>{t("Filter Set", "Filter Set")}</Form.Label>
            <Form.Select
              value={newFilterSetId ?? activeSetId ?? ""}
              onChange={(e) => setNewFilterSetId(Number(e.target.value))}
              className="bg-dark text-light border-secondary"
            >
              {filterSets?.map((fs) => (
                <option key={fs.id} value={fs.id || 0}>
                  {fs.name}
                </option>
              ))}
            </Form.Select>
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>{t("Filter Type", "Filter Type")}</Form.Label>
            <Form.Select
              value={newFilterType}
              onChange={(e) => setNewFilterType(e.target.value as "reason" | "amount")}
              className="bg-dark text-light border-secondary"
            >
              <option value="reason">{t("Reason (Text)", "Reason (Text)")}</option>
              <option value="amount">{t("Amount (Number)", "Amount (Number)")}</option>
            </Form.Select>
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>{t("Match Type", "Match Type")}</Form.Label>
            <Form.Select
              value={newMatchType}
              onChange={(e) => setNewMatchType(e.target.value as "exact" | "contains")}
              className="bg-dark text-light border-secondary"
            >
              <option value="exact">{t("Exact Match", "Exact Match")}</option>
              <option value="contains">{t("Contains", "Contains")}</option>
            </Form.Select>
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>{t("Value", "Value")}</Form.Label>
            <Form.Control
              type={newFilterType === "amount" ? "number" : "text"}
              value={newFilterValue}
              onChange={(e) => setNewFilterValue(e.target.value)}
              placeholder={newFilterType === "amount" ? "10000000" : t("e.g. SRP or Reimbursement", "e.g. SRP or Reimbursement")}
              className="bg-dark text-light border-secondary"
            />
          </Form.Group>
        </BaseModal>
      )}

      {/* Delete Confirmation Modals */}
      {filterSetToDelete !== null && (
        <BaseModal
          show={filterSetToDelete !== null}
          onHide={() => setFilterSetToDelete(null)}
          size={ModalSize.medium}
          title={<span className="h5 text-danger mb-0">{t("Delete Filter Set", "Delete Filter Set")}</span>}
          footer={
            <>
              <Button variant="secondary" onClick={() => setFilterSetToDelete(null)}>
                {t("Cancel", "Cancel")}
              </Button>
              <Button
                variant="danger"
                disabled={deleteSetMutation.isPending}
                onClick={() => deleteSetMutation.mutate(filterSetToDelete)}
              >
                {deleteSetMutation.isPending && <Spinner size="sm" animation="border" className="me-1" />}
                {t("Delete", "Delete")}
              </Button>
            </>
          }
        >
          <p className="mb-0">{t("Are you sure you want to delete this filter set?", "Are you sure you want to delete this filter set?")}</p>
        </BaseModal>
      )}

      {filterToDelete !== null && (
        <BaseModal
          show={filterToDelete !== null}
          onHide={() => setFilterToDelete(null)}
          size={ModalSize.medium}
          title={<span className="h5 text-danger mb-0">{t("Delete Filter", "Delete Filter")}</span>}
          footer={
            <>
              <Button variant="secondary" onClick={() => setFilterToDelete(null)}>
                {t("Cancel", "Cancel")}
              </Button>
              <Button
                variant="danger"
                disabled={deleteFilterMutation.isPending}
                onClick={() => deleteFilterMutation.mutate(filterToDelete)}
              >
                {deleteFilterMutation.isPending && <Spinner size="sm" animation="border" className="me-1" />}
                {t("Delete", "Delete")}
              </Button>
            </>
          }
        >
          <p className="mb-0">{t("Are you sure you want to delete this filter?", "Are you sure you want to delete this filter?")}</p>
        </BaseModal>
      )}
    </div>
  );
}

export default FiltersTab;
