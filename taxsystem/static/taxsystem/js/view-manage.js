/* global aaTaxSystemSettings, aaTaxSystemSettingsOverride, _bootstrapTooltip, fetchGet, fetchPost, DataTable, numberFormatter, moment, tablePaymentSystem */
$(document).ready(function() {
    /**
     * Modals :: IDs
     */
    // Table :: Tax Accounts
    const modalRequestSwitchUser = $('#taxsystem-accept-switch-tax-account');
    const modalRequestViewPayments = $('#taxsystem-view-tax-account');
    const modalRequestAcceptBulkActions = $('#taxsystem-accept-bulk-actions');
    // Modal :: Table :: Payments
    const modalRequestAddPayment = $('#taxsystem-accept-add-payment');
    const modalRequestApprovePayment = $('#taxsystem-accept-approve-payment');
    const modalRequestUndoPayment = $('#taxsystem-accept-undo-payment');
    const modalRequestDeletePayment = $('#taxsystem-accept-delete-payment');
    const modalRequestRejectPayment = $('#taxsystem-accept-reject-payment');
    const modalRequestViewPaymentsDetails = $('#taxsystem-view-payment-details');
    // Sub Modal :: Payments Details :: Tables
    const paymentInformationTable = $('#payment-information-table');
    const paymentDashboardTable = $('#payment-dashboard-table');
    const paymentHistoryTable = $('#payment-history-table');
    // Modal :: Table :: Members
    const modalRequestDeleteMember = $('#taxsystem-accept-delete-member');
    /**
     * Table :: IDs
     */
    const membersTable = $('#members');
    const taxAccountsTable = $('#tax-accounts');
    const paymentsTable = $('#payments-table');

    /**
     * Dashboard :: Helper Function :: Fetch and Populate Statistics Data
     * Receives data object and populates the statistics fields in the dashboard
     * @param {Object} newData - Data object containing statistics information
     * @private
     */
    const _fetchAndPopulateDashboardStatistics = (newData) => {
        /**
         * Dashboard :: Statistics :: Data
         */
        const statistics = newData.statistics;

        $('#statistics_payment_users').text(statistics.tax_account.accounts);
        $('#statistics_payment_users_active').text(statistics.tax_account.accounts_active);
        $('#statistics_payment_users_inactive').text(statistics.tax_account.accounts_inactive);
        $('#statistics_payment_users_deactivated').text(statistics.tax_account.accounts_deactivated);
        $('#psystem_payment_users_paid').text(statistics.tax_account.accounts_paid);
        $('#psystem_payment_users_unpaid').text(statistics.tax_account.accounts_unpaid);

        /**
         * Dashboard :: Statistics :: Payments
         */
        $('#statistics_payments').text(statistics.payments.payments);
        $('#statistics_payments_pending').text(statistics.payments.payments_pending);
        $('#statistics_payments_auto').text(statistics.payments.payments_automatic);
        $('#statistics_payments_manually').text(statistics.payments.payments_manual);

        /**
         * Dashboard :: Statistics :: Members
         */
        $('#statistics_members').text(statistics.members.members);
        $('#statistics_members_mains').text(statistics.members.members_mains);
        $('#statistics_members_alts').text(statistics.members.members_alts);
        $('#statistics_members_not_registered').text(statistics.members.members_unregistered);
    };

    /**
     * Helper function: Filter DataTable using DataTables custom search API
     * @param {Function} predicate - Predicate function to filter rows
     * @param {Object} dt - DataTable instance
     */
    const applyPaymentFilter = (predicate, dt) => {
        // reset custom filters and add a table-scoped predicate
        _resetBulkState();
        $.fn.dataTable.ext.search = [];
        $.fn.dataTable.ext.search.push(function(settings, searchData, index, rowData) {
            // only apply to this DataTable instance
            try {
                if (settings.nTable !== dt.table().node()) {
                    return true;
                }
            } catch (e) {
                return true;
            }

            if (!rowData) return true;
            return predicate(rowData);
        });
        dt.draw();
    };

    fetchGet({
        url: aaTaxSystemSettings.url.Dashboard
    })
        .then((data) => {
            if (data) {
            /**
             * Dashboard :: Information
             */
                const TaxAmount = numberFormatter({
                    value: parseFloat(data.tax_amount),
                    language: aaTaxSystemSettings.locale,
                    options: {
                        style: 'currency',
                        currency: 'ISK'
                    }
                });
                const TaxPeriod = parseFloat(data.tax_period);
                const ActivityFormatted = numberFormatter({
                    value: data.activity,
                    options: {
                        style: 'currency',
                        currency: 'ISK',
                        maximumFractionDigits: 0
                    }
                });
                const ActivityClass = data.activity >= 0 ? 'text-success' : 'text-danger';

                /**
             * Dashboard :: Set Information
             */
                $('#dashboard-info').html(data.owner.owner_name);
                $('#activity').html(`<span class="${ActivityClass}">${ActivityFormatted}</span>`);
                $('#taxamount').attr('data-value', parseFloat(data.tax_amount)).text(`${TaxAmount}`);
                $('#period').attr('data-value', TaxPeriod).text(`${TaxPeriod} ${aaTaxSystemSettings.translations.days}`);

                /**
             * Dashboard :: Editable Fields
             */
                $('#taxamount').editable({
                    container: 'body',
                    type: 'number',
                    title: aaTaxSystemSettings.translations.editable.title.taxamount,
                    display: () => {
                        return false;
                    },
                    success: function(response, newValue) {
                        fetchPost({
                            url: aaTaxSystemSettings.url.UpdateTax,
                            csrfToken: aaTaxSystemSettings.csrfToken,
                            payload: {
                                tax_amount: newValue
                            }
                        })
                            .then((data) => {
                                if (data) {
                                    const newValueFormatted = numberFormatter({
                                        value: parseInt(newValue),
                                        locales: aaTaxSystemSettings.locale,
                                        options: {
                                            style: 'currency',
                                            currency: 'ISK'
                                        }
                                    });
                                    console.log(newValueFormatted);
                                    $('#taxamount').text(newValueFormatted);
                                }
                            })
                            .catch((error) => {
                                console.error('Error updating Tax Amount:', error);
                            });
                    },
                    validate: function(value) {
                        if (value === '') {
                            return aaTaxSystemSettings.translations.editable.validate.required;
                        } else if (isNaN(value) || parseFloat(value) < 0) {
                            return aaTaxSystemSettings.translations.editable.validate.min_value;
                        }
                    }
                });

                $('#period').editable({
                    container: 'body',
                    type: 'number',
                    pk: data.owner.owner_id,
                    url: aaTaxSystemSettings.url.UpdatePeriod,
                    title: aaTaxSystemSettings.translations.editable.title.period,
                    display: () => {
                        return false;
                    },
                    success: function(response, newValue) {
                        fetchPost({
                            url: aaTaxSystemSettings.url.UpdatePeriod,
                            csrfToken: aaTaxSystemSettings.csrfToken,
                            payload: {
                                tax_period: newValue
                            }
                        })
                            .then((data) => {
                                if (data) {
                                    console.log(newValue);
                                    $('#period').text(parseInt(newValue));
                                }
                            })
                            .catch((error) => {
                                console.error('Error updating Tax Amount:', error);
                            });
                    },
                    validate: function(value) {
                        if (value === '') {
                            return 'This field is required';
                        } else if (isNaN(value) || parseInt(value) < 1) {
                            return 'Please enter a valid positive integer';
                        }
                    }
                });

                /**
             * Dashboard :: Update Status
             */
                $('#update_status_icon').html(data.update_status.icon);
                $('#update_wallet').html(data.update_status.status.wallet && data.update_status.status.wallet.last_run_finished_at
                    ? moment(data.update_status.status.wallet.last_run_finished_at).fromNow()
                    : 'N/A');
                $('#update_divisions').html(data.update_status.status.divisions && data.update_status.status.divisions.last_run_finished_at
                    ? moment(data.update_status.status.divisions.last_run_finished_at).fromNow()
                    : 'N/A');
                $('#update_division_name').html(data.update_status.status.division_names && data.update_status.status.division_names.last_run_finished_at
                    ? moment(data.update_status.status.division_names.last_run_finished_at).fromNow()
                    : 'N/A');
                $('#update_members').html(data.update_status.status.members && data.update_status.status.members.last_run_finished_at
                    ? moment(data.update_status.status.members.last_run_finished_at).fromNow()
                    : 'N/A');
                $('#update_payments').html(data.update_status.status.payments && data.update_status.status.payments.last_run_finished_at
                    ? moment(data.update_status.status.payments.last_run_finished_at).fromNow()
                    : 'N/A');
                $('#update_deadlines').html(data.update_status.status.deadlines && data.update_status.status.deadlines.last_run_finished_at
                    ? moment(data.update_status.status.deadlines.last_run_finished_at).fromNow()
                    : 'N/A');

                /**
             * Dashboard :: Division :: Data
             */
                const divisionsData = data.divisions;
                const divisions = divisionsData.divisions;
                if (!divisions || divisions.length === 0) {
                    for (let i = 1; i <= 7; i++) {
                        $(`#division${i}_name`).show();
                        $(`#division${i}`).text('N/A').show();
                    }
                } else {
                    for (let i = 0; i < divisions.length; i++) {
                        const division = divisions[i];
                        try {
                            if (division && division.name && division.balance) {
                                $(`#division${i + 1}_name`).text(division.name);
                                $(`#division${i + 1}`).text(
                                    numberFormatter({
                                        value: division.balance,
                                        options: {
                                            style: 'currency',
                                            currency: 'ISK',
                                            maximumFractionDigits: 0
                                        }
                                    })
                                );
                            } else {
                                $(`#division${i + 1}_name`).hide();
                                $(`#division${i + 1}`).hide();
                            }
                        } catch (e) {
                            console.error(`Error fetching division data for division ${i + 1}:`, e);
                            $(`#division${i + 1}_name`).hide();
                            $(`#division${i + 1}`).hide();
                        }
                    }
                }

                /**
            * Dashboard :: Division :: Total Balance
            */
                if (!divisions || divisions.length === 0) {
                    $('#total_balance').text('N/A');
                } else {
                    $('#total_balance').text(
                        numberFormatter({
                            value: divisionsData.total_balance,
                            language: aaTaxSystemSettings.locale,
                            options: {
                                style: 'currency',
                                currency: 'ISK',
                                maximumFractionDigits: 0
                            }
                        })
                    );
                }

                /**
             * Dashboard :: Statistics
             */
                _fetchAndPopulateDashboardStatistics(data);

                /**
             * Bootstrap Tooltips
             */
                _bootstrapTooltip();
            }
        })
        .catch((error) => {
            console.error('Error fetching Dashboard Data:', error);
        });

    /**
     * Table :: Members
     */
    fetchGet({
        url: aaTaxSystemSettings.url.Members
    })
        .then((data) => {
            if (data) {
                const MembersDataTable = new DataTable(membersTable, {
                    data: data,
                    language: aaTaxSystemSettings.dataTables.language,
                    layout: aaTaxSystemSettings.dataTables.layout,
                    ordering: aaTaxSystemSettings.dataTables.ordering,
                    columnControl: aaTaxSystemSettings.dataTables.columnControl,
                    order: [[3, 'desc']],
                    columns: [
                        { data: 'character.character_portrait' },
                        { data: 'character.character_name' },
                        { data: 'status' },
                        {
                            data: {
                                display: (data) => {
                                    const date = moment(data.joined);
                                    if (!data.joined || !date.isValid()) {
                                        return 'N/A';
                                    }
                                    return date.fromNow();
                                },
                                sort: (data) => data.joined,
                                filter: (data) => data.joined
                            }
                        },
                        {
                            data: 'actions',
                            className: 'text-end'
                        },
                    ],
                    columnDefs: [
                        {
                            targets: [0, 2, 4],
                            orderable: false,
                            columnControl: [
                                {target: 0, content: []},
                                {target: 1, content: []}
                            ]
                        },
                        {
                            targets: [0, 4],
                            width: 32
                        },
                    ],
                    initComplete: function () {
                        const dt = membersTable.DataTable();

                        $('#request-filter-members-all').on('change click', () => {
                            applyPaymentFilter(() => true, dt);
                        });

                        $('#request-filter-members-not-registered').on('change click', () => {
                            applyPaymentFilter(rowData => rowData.is_noaccount, dt);
                        });

                        $('#request-filter-members-missing').on('change click', () => {
                            applyPaymentFilter(rowData => rowData.is_missing, dt);
                        });

                        _bootstrapTooltip({selector: '#members'});
                    },
                    drawCallback: function () {
                        _bootstrapTooltip({selector: '#members'});
                    },
                    rowCallback: function(row, data) {
                        if (data.is_missing || data.is_noaccount) {
                            $(row).addClass('tax-red tax-hover');
                        }
                    },
                });
            }
        })
        .catch((error) => {
            console.error('Error fetching Members DataTable:', error);
        });

    /**
     * Table :: Tax Accounts :: Bulk Actions :: Update Bulk State
     * Updates the bulk action panel based on the number of selected checkboxes
     */
    const _updateBulkState = () => {
        const count = $(taxAccountsTable).find('.tax-row-select:checked').length;
        $('#tax-bulk-count').text(count);
        if (count > 0) {
            $('#tax-bulk-panel').removeClass('d-none').addClass('show');
        } else {
            $('#tax-bulk-panel').removeClass('show').addClass('d-none');
        }
    };
    /**
     * Table :: Tax Accounts :: Bulk Actions :: Reset States
     * Resets the bulk action panel and unchecks all selected checkboxes
     */
    const _resetBulkState = () => {
        $(taxAccountsTable).find('.tax-row-select').prop('checked', false);
        $('#tax-bulk-panel').addClass('d-none').removeClass('show');
    };

    /**
     * Table :: Tax Accounts :: Bulk Actions :: Clear Selection Button Click Handler
     * Resets the bulk action panel and unchecks all selected checkboxes
     */
    $('#tax-bulk-action-clear-selection').on('click', () => {
        _resetBulkState();
    });

    /**
     * Table :: Tax Accounts :: Bulk Actions :: Approve Button Click Handler
     * Open Approve Bulk Action Modal
     * On Confirmation send a request to the API Endpoint, reload the Tax Accounts DataTable and update Dashboard statistics, close the modal
     */
    modalRequestAcceptBulkActions.on('show.bs.modal', (event) => {
        const button = $(event.relatedTarget);
        const action = button.data('bulk-action');
        const selectedRows = $(taxAccountsTable).find('.tax-row-select:checked').closest('tr');
        const pks = selectedRows.map(function () {
            return $(this).find('.tax-row-select').data('account-pk');
        }).get().filter(Boolean);

        modalRequestAcceptBulkActions.find('#modal-button-confirm-accept-request').on('click', () => {
            fetchPost({
                url: aaTaxSystemSettings.url.BulkActions,
                csrfToken: aaTaxSystemSettings.csrfToken,
                payload: {
                    pks: pks,
                    action: action
                }
            })
                .then((data) => {
                    if (data.success === true) {
                        _reloadChangedData();
                        _resetBulkState();
                    }
                })
                .catch((error) => {
                    console.error(`Error posting approve request: ${error.message}`);
                });
            modalRequestAcceptBulkActions.modal('hide');
        });
    })
        .on('hide.bs.modal', () => {
            modalRequestAcceptBulkActions.find('#modal-button-confirm-accept-request').unbind('click');
        });

    /**
     * Table :: Tax Accounts
     */
    fetchGet({
        url: aaTaxSystemSettings.url.TaxAccounts
    })
        .then((data) => {
            if (data) {
                const PaymentSystemDataTable = new DataTable(taxAccountsTable, {
                    data: data,
                    language: aaTaxSystemSettings.dataTables.language,
                    layout: aaTaxSystemSettings.dataTables.layout,
                    ordering: aaTaxSystemSettings.dataTables.ordering,
                    columnControl: aaTaxSystemSettings.dataTables.columnControl,
                    order: [[1, 'asc']],
                    columns: [
                        { data: 'account.character_portrait' },
                        { data: 'account.character_name' },
                        { data: 'status' },
                        {
                            data: {
                                display: (data) => numberFormatter({
                                    value: data.deposit,
                                    options: {
                                        style: 'currency',
                                        currency: 'ISK'
                                    }
                                }),
                                sort: (data) => data.deposit,
                                filter: (data) => data.deposit
                            }
                        },
                        {
                            data: {
                                display: (data) => data.has_paid.display,
                                sort: (data) => data.has_paid.sort,
                                filter: (data) => data.has_paid.sort
                            }
                        },
                        {
                            data: {
                                display: (data) => {
                                    const date = moment(data.last_paid);
                                    if (!data.last_paid || !date.isValid()) {
                                        return 'N/A';
                                    }
                                    return date.fromNow();
                                },
                                sort: (data) => data.last_paid,
                                filter: (data) => data.last_paid
                            }
                        },
                        {
                            data: {
                                display: (data) => {
                                    const date = moment(data.next_due);
                                    if (!data.next_due || !date.isValid()) {
                                        return 'N/A';
                                    }
                                    return date.fromNow();
                                },
                                sort: (data) => data.next_due,
                                filter: (data) => data.next_due
                            }
                        },
                        { data: 'actions' },
                    ],
                    columnDefs: [
                        {
                            targets: [0, 4, 7],
                            orderable: false,
                            columnControl: [
                                {target: 0, content: []},
                                {target: 1, content: []}
                            ]
                        },
                        {
                            targets: [3],
                            type: 'num'
                        },
                        {
                            targets: [0, 4],
                            width: 32
                        },
                        {
                            targets: [7],
                            width: 70
                        },
                    ],
                    initComplete: function () {
                        const dt = taxAccountsTable.DataTable();

                        // per-row checkbox change handler
                        $(taxAccountsTable).on('change', '.tax-row-select', function () {
                            _updateBulkState();
                        });

                        $('#request-filter-accounts-all').on('change click', () => {
                            applyPaymentFilter(() => true, dt);
                        });

                        $('#request-filter-accounts-paid').on('change click', () => {
                            applyPaymentFilter(rowData => !!(rowData.has_paid && rowData.has_paid.raw && rowData.is_active), dt);
                        });

                        $('#request-filter-accounts-not-paid').on('change click', () => {
                            applyPaymentFilter(rowData => rowData.is_active && !(rowData.has_paid && rowData.has_paid.raw), dt);
                        });

                        _bootstrapTooltip({selector: '#tax-accounts'});
                    },
                    drawCallback: function () {
                        _bootstrapTooltip({selector: '#tax-accounts'});
                    },
                    rowCallback: function(row, data) {
                        if (!data.is_active) {
                            $(row).addClass('tax-warning tax-hover');
                        } else if (data.is_active && data.has_paid && data.has_paid.raw) {
                            $(row).addClass('tax-green tax-hover');
                        } else if (data.is_active && data.has_paid && !data.has_paid.raw) {
                            $(row).addClass('tax-red tax-hover');
                        }
                    },
                });
            }
        })
        .catch((error) => {
            console.error('Error fetching Tax Account DataTable:', error);
        });

    /**
     * Function :: Reload Changed Data
     * Handle reloading of changed data in Dashboard and Tax Accounts DataTable
     * @param {Array} newData
     */
    function _reloadChangedData() {
        fetchGet({
            url: aaTaxSystemSettings.url.Dashboard
        })
            .then((newData) => {
                if (newData) {
                    _fetchAndPopulateDashboardStatistics(newData);
                }
            })
            .catch((error) => {
                console.error('Error fetching Dashboard Data:', error);
            });
        fetchGet({
            url: aaTaxSystemSettings.url.TaxAccounts
        })
            .then((newData) => {
                if (newData) {
                    _reloadTaxAccountsDataTable(newData);
                }
            })
            .catch((error) => {
                console.error('Error fetching Tax Accounts DataTable:', error);
            });
    }

    /**
     * Table :: Tax Accounts :: Helper Function :: Reload DataTable
     * Handle reloading of Tax Accounts DataTable with new data
     * @param {Array} newData
     * @private
     */
    function _reloadTaxAccountsDataTable(newData) {
        const dtTaxAccounts = taxAccountsTable.DataTable();
        dtTaxAccounts.clear().rows.add(newData).draw();
    }

    /**
     * Modal :: Tax Accounts :: Switch User Button Click Handler
     * Open Switch Tax Account Modal
     * On Confirmation send a request to the API Endpoint, reload the Tax Accounts DataTable and close the modal
     */
    modalRequestSwitchUser.on('show.bs.modal', (event) => {
        const button = $(event.relatedTarget);
        const url = button.data('action');
        const csrfMiddlewareToken = aaTaxSystemSettings.csrfToken;

        modalRequestSwitchUser.find('#modal-button-confirm-accept-request').on('click', () => {
            fetchPost({
                url: url,
                csrfToken: csrfMiddlewareToken,
            })
                .then((data) => {
                    if (data.success === true) {
                        _reloadChangedData();
                    }
                })
                .catch((error) => {
                    console.error(`Error posting switch user request: ${error.message}`);
                });
            modalRequestSwitchUser.modal('hide');
        });
    })
        .on('hide.bs.modal', () => {
            modalRequestSwitchUser.find('#modal-button-confirm-accept-request').unbind('click');
        });

    /**
     * Modal :: Tax Accounts :: Add Payment Button Click Handler
     * Open Add Tax Account Modal
     * On Confirmation send a request to the API Endpoint, reload the Tax Accounts DataTable and close the modal
     */
    const modalRequestAddPaymentDecline = modalRequestAddPayment.find('#request-required-field');
    modalRequestAddPayment.on('show.bs.modal', (event) => {
        const button = $(event.relatedTarget);
        const url = button.data('action');
        const form = modalRequestAddPayment.find('form');
        const csrfMiddlewareToken = form.find('input[name="csrfmiddlewaretoken"]').val();

        modalRequestAddPayment.find('#modal-button-confirm-accept-request').on('click', () => {
            const addInfo = form.find('textarea[name="comment"]');
            const addInfoValue = addInfo.val();

            const addAmount = form.find('input[name="amount"]');
            const addAmountValue = addAmount.val();

            if (addInfoValue === '') {
                modalRequestAddPaymentDecline.removeClass('d-none');
                addInfo.addClass('is-invalid');

                // Add shake class to the error field
                addInfo.addClass('ts-shake');

                // Remove the shake class after 3 seconds
                setTimeout(() => {
                    addInfo.removeClass('ts-shake');
                    addInfo.removeClass('is-invalid');
                }, 1500);
            } else if (addAmountValue === '' || isNaN(addAmountValue) || Number(addAmountValue) <= 0) {
                modalRequestAddPaymentDecline.removeClass('d-none');
                addAmount.addClass('is-invalid');

                // Add shake class to the error field
                addAmount.addClass('ts-shake');

                // Remove the shake class after 3 seconds
                setTimeout(() => {
                    addAmount.removeClass('ts-shake');
                    addAmount.removeClass('is-invalid');
                }, 1500);
            } else {
                fetchPost({
                    url: url,
                    csrfToken: csrfMiddlewareToken,
                    payload: {
                        amount: addAmountValue,
                        comment: addInfoValue
                    }
                })
                    .then((data) => {
                        if (data.success === true) {
                            _reloadChangedData();
                        }
                    })
                    .catch((error) => {
                        console.error(`Error posting add payment request: ${error.message}`);
                    });
                modalRequestAddPayment.modal('hide');
            }
        });
    })
        .on('hide.bs.modal', () => {
            modalRequestAddPaymentDecline.addClass('d-none');
            modalRequestAddPayment.find('form').trigger('reset');
            modalRequestAddPayment.find('input, textarea').removeClass('is-invalid');
            modalRequestAddPayment.find('input[name="amount"]').removeClass('is-invalid');
            modalRequestAddPayment.find('#modal-button-confirm-accept-request').unbind('click');
        });

    /**
     * Modal:: Payments Accounts :: Helper Function :: Load Modal DataTable
     * Load data into Payments Accounts Modal DataTable and redraw
     * @param {Object} tableData Ajax API Response Data
     * @private
     */
    const _loadPaymentsModalDataTable = (tableData) => {
        const dtPayments = paymentsTable.DataTable();
        dtPayments.clear().rows.add(tableData).draw();
    };

    /**
     * Modal:: Payments Accounts :: Helper Function :: Clear Modal DataTable
     * Clear data from Payments Accounts Modal DataTable and redraw
     * @private
     */
    const _clearPaymentsModalDataTable = () => {
        const dtPayments = paymentsTable.DataTable();
        dtPayments.clear().draw();
    };

    /**
     * Modal :: Payments Accounts :: Table :: Payments
     * Initialize DataTable for Payments Accounts Modal :: Payments Table
     * @type {*|jQuery}
     */
    const paymentsDataTable = new DataTable(paymentsTable, {
        data: null, // Loaded via API on modal open
        language: aaTaxSystemSettings.dataTables.language,
        layout: aaTaxSystemSettings.dataTables.layout,
        ordering: aaTaxSystemSettings.dataTables.ordering,
        columnControl: aaTaxSystemSettings.dataTables.columnControl,
        order: [[1, 'desc']],
        columns: [
            {
                data: {
                    display: (data) => numberFormatter({
                        value: data.amount,
                        language: aaTaxSystemSettings.locale,
                        options: {
                            style: 'currency',
                            currency: 'ISK'
                        }
                    }),
                    sort: (data) => data.amount,
                    filter: (data) => data.amount
                }
            },
            { data: 'date' },
            { data: 'request_status.status' },
            { data: 'reviser' },
            { data: 'reason' },
            { data: 'division_name' },
            { data: 'actions' },
        ],
        columnDefs: [
            {
                targets: [6],
                orderable: false,
                columnControl: [
                    {target: 0, content: []},
                    {target: 1, content: []}
                ]
            },
        ],
        initComplete: function () {
            _bootstrapTooltip({selector: '#payments-table'});
        },
        drawCallback: function () {
            _bootstrapTooltip({selector: '#payments-table'});
        },
    });

    /**
     * Sub Modal :: Payments :: Helper Function :: Load Previous Modal 'Payments Accounts'
     * Load Previous Payments Accounts Modal from API Endpoint URL
     * @param {string} apiUrl Previous Modal API Endpoint URL
     * @private
     */
    const _loadPreviousModal = (apiUrl) => {
        fetchGet({
            url: apiUrl
        })
            .then((newData) => {
                _loadPaymentsModalDataTable(newData);
                modalRequestViewPayments.modal('show');
            })
            .catch((error) => {
                console.error('Error fetching Payments Modal:', error);
            });
    };

    /**
     * Sub-Modal :: Payments :: Table :: Approve Button Click Handler
     * Open Approve Payment Modal
     * On Confirmation send a request to the API Endpoint, reload the Tax Accounts DataTable and Payments DataTable, update Dashboard statistics, close the modal
     * and reopen the previous Payments Modal
     */
    modalRequestApprovePayment.on('show.bs.modal', (event) => {
        const button = $(event.relatedTarget);
        const url = button.data('action');
        const form = modalRequestApprovePayment.find('form');
        const csrfMiddlewareToken = form.find('input[name="csrfmiddlewaretoken"]').val();

        const previousUrl = button.data('previous-modal');
        // store previous modal url in modal data for later use
        modalRequestApprovePayment.data('previous-modal', previousUrl);

        modalRequestApprovePayment.find('#modal-button-confirm-accept-request').on('click', () => {
            const approveInfo = form.find('textarea[name="comment"]');
            const approveInfoValue = approveInfo.val();

            fetchPost({
                url: url,
                csrfToken: csrfMiddlewareToken,
                payload: {
                    comment: approveInfoValue
                }
            })
                .then((data) => {
                    if (data.success === true) {
                        _reloadChangedData();
                        _loadPreviousModal(button.data('previous-modal'));
                    }
                })
                .catch((error) => {
                    console.error(`Error posting approve request: ${error.message}`);
                });
            modalRequestApprovePayment.modal('hide');
        });
    })
        .on('hide.bs.modal', () => {
        // get previous modal url from modal data
            const previousUrl = modalRequestApprovePayment.data('previous-modal');
            modalRequestApprovePayment.find('textarea[name="comment"]').val('');

            // load previous modal if apiUrl exists
            if (previousUrl) {
                _loadPreviousModal(previousUrl);
            }

            modalRequestApprovePayment.find('#modal-button-confirm-accept-request').unbind('click');
        });

    /**
     * Sub-Modal :: Payments :: Table :: Undo Button Click Handler
     * Open Undo Payment Modal
     * On Confirmation send a request to the API Endpoint, reload the Tax Accounts DataTable and Payments DataTable, update Dashboard statistics, close the modal
     * and reopen the previous Payments Modal
     */
    const modalRequestUndoDeclineError = modalRequestUndoPayment.find('#request-required-field');
    modalRequestUndoPayment.on('show.bs.modal', (event) => {
        const button = $(event.relatedTarget);
        const url = button.data('action');
        const form = modalRequestUndoPayment.find('form');
        const csrfMiddlewareToken = form.find('input[name="csrfmiddlewaretoken"]').val();

        const previousUrl = button.data('previous-modal');
        // store previous modal url in modal data for later use
        modalRequestUndoPayment.data('previous-modal', previousUrl);

        modalRequestUndoPayment.find('#modal-button-confirm-accept-request').on('click', () => {
            const undoInfo = form.find('textarea[name="comment"]');
            const undoInfoValue = undoInfo.val();
            if (undoInfoValue === '') {
                modalRequestUndoDeclineError.removeClass('d-none');
                undoInfo.addClass('is-invalid');

                // Add shake class to the error field
                undoInfo.addClass('ts-shake');

                // Remove the shake class after 3 seconds
                setTimeout(() => {
                    undoInfo.removeClass('ts-shake');
                    undoInfo.removeClass('is-invalid');
                }, 1500);
            } else {
                fetchPost({
                    url: url,
                    csrfToken: csrfMiddlewareToken,
                    payload: {
                        comment: undoInfoValue

                    }
                })
                    .then((data) => {
                        if (data.success === true) {
                            modalRequestUndoPayment.modal('hide');
                            _reloadChangedData();
                            _loadPreviousModal(button.data('previous-modal'));
                        }
                    })
                    .catch((error) => {
                        console.error(`Error posting undo request: ${error.message}`);
                    });
            }
        });
    })
        .on('hide.bs.modal', () => {
        // get previous modal url from modal data
            const previousUrl = modalRequestUndoPayment.data('previous-modal');
            modalRequestUndoPayment.find('textarea[name="comment"]').val('');

            // load previous modal if apiUrl exists
            if (previousUrl) {
                _loadPreviousModal(previousUrl);
            }

            modalRequestUndoDeclineError.addClass('d-none');
            modalRequestUndoPayment.find('#modal-button-confirm-accept-request').unbind('click');
        });

    /**
     * Sub-Modal :: Payments :: Table :: Delete Button Click Handler
     * Open Delete Payment Modal
     * On Confirmation send a request to the API Endpoint, reload the Tax Accounts DataTable and Payments DataTable, update Dashboard statistics, close the modal
     * and reopen the previous Payments Modal
     */
    const modalRequestDeleteDeclineError = modalRequestDeletePayment.find('#request-required-field');
    modalRequestDeletePayment.on('show.bs.modal', (event) => {
        const button = $(event.relatedTarget);
        const url = button.data('action');
        const form = modalRequestDeletePayment.find('form');
        const csrfMiddlewareToken = form.find('input[name="csrfmiddlewaretoken"]').val();

        const previousUrl = button.data('previous-modal');
        // store previous modal url in modal data for later use
        modalRequestDeletePayment.data('previous-modal', previousUrl);

        modalRequestDeletePayment.find('#modal-button-confirm-accept-request').on('click', () => {
            const deleteInfo = form.find('textarea[name="comment"]');
            const deleteInfoValue = deleteInfo.val();
            if (deleteInfoValue === '') {
                modalRequestDeleteDeclineError.removeClass('d-none');
                deleteInfo.addClass('is-invalid');

                // Add shake class to the error field
                deleteInfo.addClass('ts-shake');

                // Remove the shake class after 3 seconds
                setTimeout(() => {
                    deleteInfo.removeClass('ts-shake');
                    deleteInfo.removeClass('is-invalid');
                }, 1500);
            } else {
                fetchPost({
                    url: url,
                    csrfToken: csrfMiddlewareToken,
                    payload: {
                        comment: deleteInfoValue

                    }
                })
                    .then((data) => {
                        if (data.success === true) {
                            modalRequestDeletePayment.modal('hide');
                            _reloadChangedData();
                            _loadPreviousModal(button.data('previous-modal'));
                        }
                    })
                    .catch((error) => {
                        console.error(`Error posting delete request: ${error.message}`);
                    });
            }
        });
    })
        .on('hide.bs.modal', () => {
        // get previous modal url from modal data
            const previousUrl = modalRequestDeletePayment.data('previous-modal');
            modalRequestDeletePayment.find('textarea[name="comment"]').val('');

            // load previous modal if apiUrl exists
            if (previousUrl) {
                _loadPreviousModal(previousUrl);
            }

            modalRequestDeleteDeclineError.addClass('d-none');
            modalRequestDeletePayment.find('#modal-button-confirm-accept-request').unbind('click');
        });

    /**
     * Sub-Modal :: Payments :: Table :: Reject Button Click Handler
     * Open Reject Payment Modal
     * On Confirmation send a request to the API Endpoint, reload the Tax Accounts DataTable and Payments DataTable, update Dashboard statistics, close the modal
     * and reopen the previous Payments Modal
     */
    const modalRequestRejectDeclineError = modalRequestRejectPayment.find('#request-required-field');
    modalRequestRejectPayment.on('show.bs.modal', (event) => {
        const button = $(event.relatedTarget);
        const url = button.data('action');
        const form = modalRequestRejectPayment.find('form');
        const csrfMiddlewareToken = form.find('input[name="csrfmiddlewaretoken"]').val();

        const previousUrl = button.data('previous-modal');
        // store previous modal url in modal data for later use
        modalRequestRejectPayment.data('previous-modal', previousUrl);

        modalRequestRejectPayment.find('#modal-button-confirm-accept-request').on('click', () => {
            const rejectInfo = form.find('textarea[name="comment"]');
            const rejectInfoValue = rejectInfo.val();
            if (rejectInfoValue === '') {
                modalRequestRejectDeclineError.removeClass('d-none');
                rejectInfo.addClass('is-invalid');

                // Add shake class to the error field
                rejectInfo.addClass('ts-shake');

                // Remove the shake class after 3 seconds
                setTimeout(() => {
                    rejectInfo.removeClass('ts-shake');
                    rejectInfo.removeClass('is-invalid');
                }, 1500);
            } else {
                fetchPost({
                    url: url,
                    csrfToken: csrfMiddlewareToken,
                    payload: {
                        comment: rejectInfoValue

                    }
                })
                    .then((data) => {
                        if (data.success === true) {
                            modalRequestRejectPayment.modal('hide');
                            _reloadChangedData();
                            _loadPreviousModal(button.data('previous-modal'));
                        }
                    })
                    .catch((error) => {
                        console.error(`Error posting delete request: ${error.message}`);
                    });
            }
        });
    })
        .on('hide.bs.modal', () => {
        // get previous modal url from modal data
            const previousUrl = modalRequestRejectPayment.data('previous-modal');
            modalRequestRejectPayment.find('textarea[name="comment"]').val('');

            // load previous modal if apiUrl exists
            if (previousUrl) {
                _loadPreviousModal(previousUrl);
            }

            modalRequestRejectDeclineError.addClass('d-none');
            modalRequestRejectPayment.find('#modal-button-confirm-accept-request').unbind('click');
        });

    /**
     * Modal :: Payments Accounts :: Info Button Click Handler
     * @const {_loadPaymentsModalDataTable} :: Load Payments Data into Payments DataTable in the Payments Accounts Modal
     * @const {_clearPaymentsModalDataTable} :: Clear related DataTable on Close
     * When opening, fetch data from the API Endpoint defined in the button's data-action attribute
     * and load it into the Payments DataTable related to the Payments Accounts Modal
     */
    modalRequestViewPayments.on('show.bs.modal', (event) => {
        const button = $(event.relatedTarget);
        const url = button.data('action');

        // guard clause for previous Modal reload function
        if (!url) {
            return;
        }

        fetchGet({
            url: url,
        })
            .then((data) => {
                if (data) {
                    _loadPaymentsModalDataTable(data);
                }
            })
            .catch((error) => {
                console.error('Error fetching Payments Modal:', error);
            });
    })
        .on('hide.bs.modal', () => {
            _clearPaymentsModalDataTable();
        });

    /**
     * Sub Modal:: Payments Details :: Info Button :: Helper Function :: Load Modal DataTable
     * Load data into 'taxsystem-view-payment-details' Modal DataTable and redraw
     * @param {Object} data Ajax API Response Data
     * @private
     */
    const _loadTaxAccountModalDataTable = (data) => {
        // Load Payment Information
        paymentInformationTable.find('#payment-amount').text(
            numberFormatter({
                value: data.payment.amount,
                language: aaTaxSystemSettings.locale,
                options: {
                    style: 'currency',
                    currency: 'ISK'
                }
            })
        );
        paymentInformationTable.find('#payment-division').text(data.payment.division_name);
        paymentInformationTable.find('#payment-reason').text(data.payment.reason);
        // Payment Dashboard
        paymentDashboardTable.find('#tax-account').html(`${data.account.character.character_portrait} ${data.account.character.character_name}`);
        paymentDashboardTable.find('#tax-account-status').html(data.account.account_status);
        paymentDashboardTable.find('#tax-account-deposit').text(
            numberFormatter({
                value: data.account.payment_pool,
                language: aaTaxSystemSettings.locale,
                options: {
                    style: 'currency',
                    currency: 'ISK'
                }
            })
        );
        paymentDashboardTable.find('#tax-account-owner').text(data.owner.owner_name);
        // Payment Status
        $('#payment-status-badge').html(data.payment.request_status.html);
        // Load Payment History DataTable
        const dtHistory = paymentHistoryTable.DataTable();
        dtHistory.clear().rows.add(data.payment_histories).draw();
    };

    /**
     * Sub Modal:: Payments Details :: Info Button :: Helper Function :: Clear Modal DataTable
     * Clear data from 'taxsystem-view-payment-details' Modal DataTable and redraw
     * @private
     */
    const _clearPaymentAccountModalDataTable = () => {
        // Clear Payment Information
        paymentInformationTable.find('#payment-amount').text('N/A');
        paymentInformationTable.find('#payment-division').text('N/A');
        paymentInformationTable.find('#payment-reason').text('N/A');
        // Clear Payment Dashboard
        paymentDashboardTable.find('#tax-account').html('N/A');
        paymentDashboardTable.find('#tax-account-status').html('N/A');
        paymentDashboardTable.find('#tax-account-deposit').text('N/A');
        paymentDashboardTable.find('#tax-account-owner').text('N/A');
        // Clear Payment Status
        $('#payment-status-badge').html('N/A');
        // Clear Payment History DataTable
        const dtHistory = paymentHistoryTable.DataTable();
        dtHistory.clear().draw();
    };

    /**
     * Sub Modal :: Payments Details :: Table :: Payment History
     * Initialize DataTable for 'taxsystem-view-payment-details' Modal :: Payment History Table
     * @type {*|jQuery}
     */
    const paymentHistoryDataTable = new DataTable(paymentHistoryTable, {
        data: null, // Loaded via API on modal open
        language: aaTaxSystemSettings.dataTables.language,
        layout: aaTaxSystemSettings.dataTables.layout,
        ordering: aaTaxSystemSettings.dataTables.ordering,
        columnControl: aaTaxSystemSettings.dataTables.columnControl,
        order: [[1, 'desc']],
        columns: [
            { data: 'reviser' },
            { data: 'date' },
            { data: 'action' },
            { data: 'comment' },
            { data: 'status' },
        ],
        initComplete: function () {
            _bootstrapTooltip({selector: '#payment-history-table'});
        },
        drawCallback: function () {
            _bootstrapTooltip({selector: '#payment-history-table'});
        },
    });

    /**
     * Modal :: Payments :: Table :: Info Button Click Handler
     * @const {_loadPaymentAccountModalDataTable} :: Load Payments Details Data into DataTables in the 'taxsystem-view-payment-details' Modal
     * @const {_clearPaymentAccountModalDataTable} :: Clear related DataTables on Close
     * When opening, fetch data from the API Endpoint defined in the button's data-action attribute
     * and load it into the Payments Details DataTables related to the 'taxsystem-view-payment-details' Modal
     */
    modalRequestViewPaymentsDetails.on('show.bs.modal', (event) => {
        const button = $(event.relatedTarget);
        const url = button.data('action');

        const previousUrl = button.data('previous-modal');
        // store previous modal url in modal data for later use
        modalRequestViewPaymentsDetails.data('previous-modal', previousUrl);

        // guard clause for previous Modal reload function
        if (!url) {
            return;
        }

        fetchGet({
            url: url,
        })
            .then((data) => {
                if (data) {
                    _loadTaxAccountModalDataTable(data);
                }
            })
            .catch((error) => {
                console.error('Error fetching Payments Details Modal:', error);
            });
    })
        .on('hide.bs.modal', () => {
            // get previous modal url from modal data
            const previousUrl = modalRequestViewPaymentsDetails.data('previous-modal');
            // load previous modal if apiUrl exists
            if (previousUrl) {
                _loadPreviousModal(previousUrl);
            }
            _clearPaymentAccountModalDataTable();
        });

    /**
     * Members :: Table :: Delete Button Click Handler
     * Open Delete Member Modal
     * On Confirmation send a request to the API Endpoint and close the modal
     */
    const modalRequestDeleteMemberDeclineError = modalRequestDeleteMember.find('#request-required-field');
    modalRequestDeleteMember.on('show.bs.modal', (event) => {
        const button = $(event.relatedTarget);
        const url = button.data('action');
        const form = modalRequestDeleteMember.find('form');
        const csrfMiddlewareToken = form.find('input[name="csrfmiddlewaretoken"]').val();

        modalRequestDeleteMember.find('#modal-button-confirm-accept-request').on('click', () => {
            const deleteInfo = form.find('textarea[name="comment"]');
            const deleteInfoValue = deleteInfo.val();
            if (deleteInfoValue === '') {
                modalRequestDeleteMemberDeclineError.removeClass('d-none');
                deleteInfo.addClass('is-invalid');

                // Add shake class to the error field
                deleteInfo.addClass('ts-shake');

                // Remove the shake class after 3 seconds
                setTimeout(() => {
                    deleteInfo.removeClass('ts-shake');
                    deleteInfo.removeClass('is-invalid');
                }, 1500);
            } else {
                fetchPost({
                    url: url,
                    csrfToken: csrfMiddlewareToken,
                    payload: {
                        comment: deleteInfoValue

                    }
                })
                    .then((data) => {
                        if (data.success === true) {
                            modalRequestDeleteMember.modal('hide');
                        }
                    })
                    .catch((error) => {
                        console.error(`Error posting member delete request: ${error.message}`);
                    });
            }
        });
    })
        .on('hide.bs.modal', () => {
            modalRequestDeleteMember.find('textarea[name="comment"]').val('');
            modalRequestDeleteMemberDeclineError.addClass('d-none');
            modalRequestDeleteMember.find('#modal-button-confirm-accept-request').unbind('click');
        });
});
