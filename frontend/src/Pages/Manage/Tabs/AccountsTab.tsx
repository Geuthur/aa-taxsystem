// React
import { useMemo, useState } from "react";

// Third Party
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { CheckCircle2, DollarSign, Search, UserCheck, XCircle } from "lucide-react";
import { Button, Form, InputGroup, Spinner } from "react-bootstrap";
import { useTranslation } from "react-i18next";

// AA TaxSystem
import { addCustomPayment, loadTaxAccounts, switchTaxAccount } from "@/Api/ApiCalls";
import type { components } from "@/Api/OpenApi";
import { queryKeys } from "@/Api/query";
import { BaseModal, ModalSize } from "@/Components/Base/BaseModal";
import { BaseTable } from "@/Components/Base/BaseTable";
import { ButtonGroupFilter } from "@/Components/Buttons/ButtonGroupFilter";
import { getAccountColumns } from "@/Components/Tables";
import { useTableSearchState } from "@/Hooks/useTaxsystemState";
import { MemberPaymentsModal } from "@/Pages/Manage/Modals/MemberPaymentsModal";
import { formatNumber } from "@/Utils";

interface AccountsTabProps {
  ownerId: number;
}

type AccountRow = components["schemas"]["PaymentSystemSchema"];
type PaidFilter = "all" | "paid" | "unpaid";

export function AccountsTab({ ownerId }: AccountsTabProps) {
  const { t } = useTranslation();
  const queryClient = useQueryClient();
  const [search, setSearch] = useTableSearchState("accountSearch");
  const [paidFilter, setPaidFilter] = useState<PaidFilter>("all");

  // Modal State for switching account
  const [selectedAccount, setSelectedAccount] = useState<AccountRow | null>(null);
  const [newStatus, setNewStatus] = useState("active");
  const [comment, setComment] = useState("");

  // Modal State for custom payment
  const [paymentAccount, setPaymentAccount] = useState<AccountRow | null>(null);
  const [paymentAmount, setPaymentAmount] = useState<number | "">("");
  const [paymentComment, setPaymentComment] = useState("");

  // Modal State for member payments / activities
  const [historyMember, setHistoryMember] = useState<{
    characterId: number;
    characterName: string;
    characterPortrait?: string;
  } | null>(null);

  const { data: accounts, isLoading, isError } = useQuery({
    queryKey: queryKeys.TaxAccounts(ownerId),
    queryFn: () => loadTaxAccounts(ownerId),
  });

  const switchMutation = useMutation({
    mutationFn: ({ accountPk }: { accountPk: number }) =>
      switchTaxAccount(ownerId, accountPk),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.TaxAccounts(ownerId) });
      setSelectedAccount(null);
      setComment("");
    },
  });

  const addPaymentMutation = useMutation({
    mutationFn: () => {
      const targetPk = paymentAccount?.account_id;
      if (!targetPk) throw new Error("No account selected");
      return addCustomPayment(ownerId, targetPk, {
        amount: Number(paymentAmount),
        comment: paymentComment.trim(),
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: queryKeys.TaxAccounts(ownerId) });
      queryClient.invalidateQueries({ queryKey: queryKeys.Payments(ownerId) });
      setPaymentAccount(null);
      setPaymentAmount("");
      setPaymentComment("");
    },
  });

  const filteredAccounts = useMemo(() => {
    if (!accounts) return [];
    let list = accounts;
    if (paidFilter === "paid") {
      list = list.filter((acc) => Boolean(acc.has_paid));
    } else if (paidFilter === "unpaid") {
      list = list.filter((acc) => !acc.has_paid);
    }
    if (!search) return list;
    const q = search.toLowerCase();
    return list.filter(
      (acc) =>
        acc.account?.character_name?.toLowerCase().includes(q) ||
        acc.status?.toLowerCase().includes(q),
    );
  }, [accounts, search, paidFilter]);

  const columns = useMemo(
    () =>
      getAccountColumns({
        t,
        onHistory: (acc) => {
          if (acc.account?.character_id) {
            setHistoryMember({
              characterId: acc.account.character_id,
              characterName: acc.account.character_name || "",
              characterPortrait: acc.account.character_portrait,
            });
          }
        },
        onAddPayment: (acc) => {
          setPaymentAccount(acc);
          setPaymentAmount("");
          setPaymentComment("");
        },
        onSwitchStatus: (acc) => {
          setSelectedAccount(acc);
          setNewStatus(acc.is_active ? "inactive" : "active");
        },
      }),
    [t],
  );

  return (
    <div className="mt-3">
      <div className="d-flex flex-wrap justify-content-between align-items-center gap-2 mb-3">
        <div className="d-flex flex-wrap align-items-center gap-2">
          <InputGroup style={{ maxWidth: 360 }}>
            <InputGroup.Text className="bg-dark border-secondary text-secondary">
              <Search size={16} />
            </InputGroup.Text>
            <Form.Control
              type="text"
              placeholder={t("Filter accounts by name or status...")}
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="bg-dark text-light border-secondary"
            />
          </InputGroup>

          <ButtonGroupFilter<PaidFilter>
            value={paidFilter}
            onChange={(val) => setPaidFilter(val)}
            options={[
              { value: "all", label: t("All"), activeVariant: "aa-btn-primary" },
              {
                value: "paid",
                label: t("Paid"),
                icon: <CheckCircle2 size={13} />,
                activeVariant: "aa-btn-success",
              },
              {
                value: "unpaid",
                label: t("Unpaid"),
                icon: <XCircle size={13} />,
                activeVariant: "aa-btn-danger",
              },
            ]}
            ariaLabel="Filter accounts by payment status"
          />
        </div>
      </div>

      <BaseTable
        data={filteredAccounts}
        columns={columns}
        isFetching={isLoading}
        isError={isError}
        emptyText={t("No tax accounts found.")}
        variant="vowra-light"
      />

      {/* Switch Account Modal */}
      {selectedAccount && (
        <BaseModal
          show={!!selectedAccount}
          onHide={() => setSelectedAccount(null)}
          size={ModalSize.medium}
          title={
            <>
              <UserCheck size={18} className="me-2 text-primary" />
              {t("Switch Tax Account")}: {selectedAccount.account?.character_name}
            </>
          }
          footer={
            <>
              <Button
                variant="secondary"
                onClick={() => setSelectedAccount(null)}
              >
                {t("Cancel")}
              </Button>
              <Button
                variant="primary"
                disabled={switchMutation.isPending}
                onClick={() => {
                  if (selectedAccount.account_id) {
                    switchMutation.mutate({
                      accountPk: selectedAccount.account_id,
                    });
                  }
                }}
              >
                {switchMutation.isPending && <Spinner size="sm" animation="border" className="me-1" />}
                {t("Save Changes")}
              </Button>
            </>
          }
        >
          <Form.Group className="mb-3">
            <Form.Label>{t("New Status")}</Form.Label>
            <Form.Select
              value={newStatus}
              onChange={(e) => setNewStatus(e.target.value)}
              className="bg-dark text-light border-secondary"
            >
              <option value="active">{t("Active")}</option>
              <option value="inactive">{t("Inactive")}</option>
              <option value="exempt">{t("Exempt")}</option>
            </Form.Select>
          </Form.Group>
          <Form.Group className="mb-3">
            <Form.Label>{t("Comment / Reason")}</Form.Label>
            <Form.Control
              as="textarea"
              rows={3}
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder={t("Optional comment for admin history...")}
              className="bg-dark text-light border-secondary"
            />
          </Form.Group>
        </BaseModal>
      )}

      {/* Add Custom Payment Modal */}
      {paymentAccount && (
        <BaseModal
          show={!!paymentAccount}
          onHide={() => setPaymentAccount(null)}
          size={ModalSize.medium}
          title={
            <div className="d-flex align-items-center gap-2 text-success">
              <DollarSign size={18} />
              {t("Add Custom Payment")}
            </div>
          }
          footer={
            <>
              <Button
                variant="secondary"
                onClick={() => setPaymentAccount(null)}
              >
                {t("Cancel")}
              </Button>
              <Button
                variant="success"
                disabled={
                  !paymentAmount ||
                  Number(paymentAmount) <= 0 ||
                  !paymentComment.trim() ||
                  addPaymentMutation.isPending
                }
                onClick={() => addPaymentMutation.mutate()}
              >
                {addPaymentMutation.isPending && <Spinner size="sm" animation="border" className="me-1" />}
                {t("Add Payment")}
              </Button>
            </>
          }
        >
          <div className="d-flex align-items-center gap-3 mb-3 p-2 bg-black bg-opacity-25 rounded border border-secondary">
            {paymentAccount.account?.character_portrait && (
              <img
                src={paymentAccount.account.character_portrait}
                alt={paymentAccount.account.character_name}
                width={40}
                height={40}
                className="rounded-circle"
              />
            )}
            <div>
              <div className="fw-semibold text-light">{paymentAccount.account?.character_name}</div>
              <div className="small text-muted">
                {t("Current Balance")}:{" "}
                <span className="text-info">{formatNumber(Number(paymentAccount.deposit || 0))}</span>
              </div>
            </div>
          </div>

          <Form.Group className="mb-3">
            <Form.Label>{t("Amount (ISK)")}</Form.Label>
            <Form.Control
              type="number"
              min="1"
              step="1"
              value={paymentAmount}
              onChange={(e) => setPaymentAmount(e.target.value === "" ? "" : Number(e.target.value))}
              placeholder={t("e.g. 10000000")}
              className="bg-dark text-light border-secondary"
              autoFocus
            />
            {typeof paymentAmount === "number" && paymentAmount > 0 && (
              <Form.Text className="text-info small">
                ≈ {formatNumber(paymentAmount)}
              </Form.Text>
            )}
          </Form.Group>

          <Form.Group className="mb-3">
            <Form.Label>{t("Reason / Comment")}</Form.Label>
            <Form.Control
              as="textarea"
              rows={3}
              value={paymentComment}
              onChange={(e) => setPaymentComment(e.target.value)}
              placeholder={t("Reason for manual payment addition...")}
              className="bg-dark text-light border-secondary"
              required
            />
          </Form.Group>
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
    </div>
  );
}

export default AccountsTab;
