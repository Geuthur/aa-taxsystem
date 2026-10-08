// React
import { useMemo, useState } from "react";

// Third Party
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Filter, Layers, Plus } from "lucide-react";
import { Button, Card, Col, Form, Row, Spinner } from "react-bootstrap";
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
import { queryKeys } from "@/Api/query";
import { BaseModal, ModalSize } from "@/Components/Base/BaseModal";
import { BaseTable } from "@/Components/Base/BaseTable";
import { getFilterRuleColumns, getFilterSetColumns } from "@/Components/Tables";

interface FiltersTabProps {
  ownerId: number;
}

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

  const setColumns = useMemo(
    () =>
      getFilterSetColumns({
        t,
        activeSetId,
        onSelect: (id) => setSelectedFilterSetId(id),
        onDelete: (id) => setFilterSetToDelete(id),
      }),
    [t, activeSetId],
  );

  const filterTypeLabels = useMemo<Record<string, string>>(
    () => ({
      reason: t("Reason (Text)"),
      amount: t("Amount (Number)"),
    }),
    [t],
  );
  const matchTypeLabels = useMemo<Record<string, string>>(
    () => ({
      exact: t("Exact Match"),
      contains: t("Contains"),
    }),
    [t],
  );

  const filterColumns = useMemo(
    () =>
      getFilterRuleColumns({
        t,
        filterTypeLabels,
        matchTypeLabels,
        onDelete: (id) => setFilterToDelete(id),
      }),
    [t, filterTypeLabels, matchTypeLabels],
  );

  return (
    <div className="mt-3">
      <Row className="g-4">
        <Col xs={12}>
          <Card className="bg-dark border-secondary">
            <Card.Header className="d-flex align-items-center justify-content-between border-secondary">
              <h5 className="mb-0 d-flex align-items-center gap-2">
                <Layers size={18} className="text-primary" />
                {t("Filter Sets")}
              </h5>
              <Button
                className="aa-btn aa-btn-sm aa-btn-primary"
                onClick={() => setShowCreateSetModal(true)}
              >
                <Plus size={14} />
                {t("Add Filter Set")}
              </Button>
            </Card.Header>
            <Card.Body>
              <BaseTable
                data={filterSets || []}
                columns={setColumns}
                isFetching={setsLoading}
                emptyText={t("No filter sets defined.")}
              />
            </Card.Body>
          </Card>
        </Col>

        <Col xs={12}>
          <Card className="bg-dark border-secondary">
            <Card.Header className="d-flex align-items-center justify-content-between border-secondary">
              <h5 className="mb-0 d-flex align-items-center gap-2">
                <Filter size={18} className="text-info" />
                {t("Active Filters")}
              </h5>
              <Button
                className="aa-btn aa-btn-sm aa-btn-info"
                disabled={!filterSets || filterSets.length === 0}
                onClick={() => {
                  setNewFilterSetId(activeSetId);
                  setShowCreateFilterModal(true);
                }}
              >
                <Plus size={14} />
                {t("Add Filter")}
              </Button>
            </Card.Header>
            <Card.Body>
              <BaseTable
                data={filters || []}
                columns={filterColumns}
                isFetching={filtersLoading}
                emptyText={t("No active filters found.")}
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
              {t("Add Filter Set")}
            </div>
          }
          footer={
            <>
              <Button
                variant="secondary"
                onClick={() => setShowCreateSetModal(false)}
              >
                {t("Cancel")}
              </Button>
              <Button
                variant="primary"
                disabled={!newSetName.trim() || createSetMutation.isPending}
                onClick={() => createSetMutation.mutate()}
              >
                {createSetMutation.isPending && <Spinner size="sm" animation="border" className="me-1" />}
                {t("Create")}
              </Button>
            </>
          }
        >
          <Form.Group className="mb-3">
            <Form.Label>{t("Name")}</Form.Label>
            <Form.Control
              type="text"
              value={newSetName}
              onChange={(e) => setNewSetName(e.target.value)}
              placeholder={t("e.g. Corp Tax Exemption")}
              className="bg-dark text-light border-secondary"
              autoFocus
            />
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>{t("Description")}</Form.Label>
            <Form.Control
              type="text"
              value={newSetDescription}
              onChange={(e) => setNewSetDescription(e.target.value)}
              placeholder={t("Optional description")}
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
              {t("Add Filter")}
            </div>
          }
          footer={
            <>
              <Button
                variant="secondary"
                onClick={() => setShowCreateFilterModal(false)}
              >
                {t("Cancel")}
              </Button>
              <Button
                variant="info"
                disabled={!newFilterValue.trim() || createFilterMutation.isPending}
                onClick={() => createFilterMutation.mutate()}
              >
                {createFilterMutation.isPending && <Spinner size="sm" animation="border" className="me-1" />}
                {t("Create")}
              </Button>
            </>
          }
        >
          <Form.Group className="mb-3">
            <Form.Label>{t("Filter Set")}</Form.Label>
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
            <Form.Label>{t("Filter Type")}</Form.Label>
            <Form.Select
              value={newFilterType}
              onChange={(e) => setNewFilterType(e.target.value as "reason" | "amount")}
              className="bg-dark text-light border-secondary"
            >
              <option value="reason">{t("Reason (Text)")}</option>
              <option value="amount">{t("Amount (Number)")}</option>
            </Form.Select>
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>{t("Match Type")}</Form.Label>
            <Form.Select
              value={newMatchType}
              onChange={(e) => setNewMatchType(e.target.value as "exact" | "contains")}
              className="bg-dark text-light border-secondary"
            >
              <option value="exact">{t("Exact Match")}</option>
              <option value="contains">{t("Contains")}</option>
            </Form.Select>
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>{t("Value")}</Form.Label>
            <Form.Control
              type={newFilterType === "amount" ? "number" : "text"}
              value={newFilterValue}
              onChange={(e) => setNewFilterValue(e.target.value)}
              placeholder={newFilterType === "amount" ? "10000000" : t("e.g. SRP or Reimbursement")}
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
          title={<span className="h5 text-danger mb-0">{t("Delete Filter Set")}</span>}
          footer={
            <>
              <Button
                variant="secondary"
                onClick={() => setFilterSetToDelete(null)}
              >
                {t("Cancel")}
              </Button>
              <Button
                variant="danger"
                disabled={deleteSetMutation.isPending}
                onClick={() => deleteSetMutation.mutate(filterSetToDelete)}
              >
                {deleteSetMutation.isPending && <Spinner size="sm" animation="border" className="me-1" />}
                {t("Delete")}
              </Button>
            </>
          }
        >
          <p className="mb-0">{t("Are you sure you want to delete this filter set?")}</p>
        </BaseModal>
      )}

      {filterToDelete !== null && (
        <BaseModal
          show={filterToDelete !== null}
          onHide={() => setFilterToDelete(null)}
          size={ModalSize.medium}
          title={<span className="h5 text-danger mb-0">{t("Delete Filter")}</span>}
          footer={
            <>
              <Button
                variant="secondary"
                onClick={() => setFilterToDelete(null)}
              >
                {t("Cancel")}
              </Button>
              <Button
                variant="danger"
                disabled={deleteFilterMutation.isPending}
                onClick={() => deleteFilterMutation.mutate(filterToDelete)}
              >
                {deleteFilterMutation.isPending && <Spinner size="sm" animation="border" className="me-1" />}
                {t("Delete")}
              </Button>
            </>
          }
        >
          <p className="mb-0">{t("Are you sure you want to delete this filter?")}</p>
        </BaseModal>
      )}
    </div>
  );
}

export default FiltersTab;
