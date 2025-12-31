/* global aaTaxSystemSettings, aaTaxSystemSettingsOverride, _bootstrapTooltip, fetchGet, fetchPost, DataTable, numberFormatter */

$(document).ready(() => {
    // Table :: ID
    const paymentsTable = $('#payments');
    // Sub Modal :: Payments Details :: Tables
    const paymentInformationTable = $('#payment-information-table');
    const paymentAccountTable = $('#payment-account-table');
    const paymentHistoryTable = $('#payment-history-table');
    // Modal :: Payments Details
    const modalRequestViewPaymentsDetails = $('#taxsystem-view-payment-details');
    const modalRequestApprovePayment = $('#taxsystem-accept-approve-payment');
    const modalRequestRejectPayment = $('#taxsystem-accept-reject-payment');
    const modalRequestUndoPayment = $('#taxsystem-accept-undo-payment');
    const modalRequestDeletePayment = $('#taxsystem-accept-delete-payment');
    const modalRequestAcceptBulkActions = $('#taxsystem-accept-bulk-actions');

    fetchGet({
        url: aaTaxSystemSettings.url.Payments
    })
        .then((data) => {
            if (data) {
            /**
             * Table :: Payments
             */
                const paymentsDataTable = new DataTable(paymentsTable, {
                    data: data,
                    language: aaTaxSystemSettings.dataTables.language,
                    layout: aaTaxSystemSettings.dataTables.layout,
                    ordering: aaTaxSystemSettings.dataTables.ordering,
                    columnControl: aaTaxSystemSettings.dataTables.columnControl,
                    order: [[3, 'desc']],
                    columnDefs: [
                        {
                            targets: [0, 5],
                            orderable: false,
                            columnControl: [
                                {target: 0, content: []},
                                {target: 1, content: []}
                            ]
                        },
                        {
                            targets: [0,5],
                            width: 32
                        },
                        { targets: [2], type: 'num' },
                        { targets: [3], type: 'date' }
                    ],
                    columns: [
                        { data: 'character.character_portrait' },
                        { data: 'character.character_name' },
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
                        { data: 'actions' },
                    ],
                    initComplete: function () {
                        const dt = paymentsTable.DataTable();

                        /**
                         * Helper function: Filter DataTable using DataTables custom search API
                         */
                        const applyPaymentFilter = (predicate) => {
                            // reset custom filters and add a table-scoped predicate
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

                        $('#request-filter-all').on('change click', () => {
                            applyPaymentFilter(() => true);
                        });

                        $('#request-filter-pending').on('change click', () => {
                            applyPaymentFilter(rowData => !!(rowData.request_status && (rowData.request_status.color === 'info' || rowData.request_status.color === 'warning')));
                        });

                        // per-row checkbox change handler
                        $(paymentsTable).on('change', '.tax-row-select', function () {
                            _updateBulkState();
                        });

                        // clear on next page
                        paymentsTable.on('page.dt', () => {
                            _resetBulkState();
                        });
                    },
                    drawCallback: function () {
                        _bootstrapTooltip({selector: '#payments'});
                    },
                    rowCallback: function(row, data) {
                        if (data.request_status && (data.request_status.color === 'info' || data.request_status.color === 'warning')) {
                            $(row).addClass('tax-warning tax-hover');
                        }
                    },
                });
            }
        })
        .catch((error) => {
            console.error('Error fetching Payments DataTable:', error);
        });

    /**
     * Sub Modal:: Payments Details :: Info Button :: Helper Function :: Load Modal DataTable
     * Load data into 'taxsystem-view-payment-details' Modal DataTable and redraw
     * @param {Object} data Ajax API Response Data
     * @private
     */
    const _loadPaymentAccountModalDataTable = (data) => {
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
        paymentAccountTable.find('#tax-account-user').html(`${data.account.character.character_portrait} ${data.account.character.character_name}`);
        paymentAccountTable.find('#tax-account-status').html(data.account.account_status);
        paymentAccountTable.find('#tax-account-deposit').text(
            numberFormatter({
                value: data.account.payment_pool,
                language: aaTaxSystemSettings.locale,
                options: {
                    style: 'currency',
                    currency: 'ISK'
                }
            })
        );
        paymentAccountTable.find('#tax-account-owner').text(data.owner.owner_name);
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
        paymentAccountTable.find('#tax-account-user').html('N/A');
        paymentAccountTable.find('#tax-account-status').html('N/A');
        paymentAccountTable.find('#tax-account-deposit').text('N/A');
        paymentAccountTable.find('#tax-account-owner').text('N/A');
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
                    _loadPaymentAccountModalDataTable(data);
                }
            })
            .catch((error) => {
                console.error('Error fetching Payments Details Modal:', error);
            });
    })
        .on('hide.bs.modal', () => {
            _clearPaymentAccountModalDataTable();
        });


    /**
     * Table :: Payments :: Helper Function :: Reload DataTable
     * Handle reloading of Payments DataTable with new data
     * @param {Array} newData
     * @private
     */
    function _reloadPaymentsDataTable() {
        fetchGet({
            url: aaTaxSystemSettings.url.Payments
        })
            .then((data) => {
                if (data) {
                    const dtPayments = paymentsTable.DataTable();
                    dtPayments.clear().rows.add(data).draw();
                }
            })
            .catch((error) => {
                console.error('Error fetching Payments DataTable:', error);
            });
    }

    /**
     * Table :: Payments :: Approve Button Click Handler
     * Open Approve Payment Modal
     * On Confirmation send a request to the API Endpoint, reload the Payments DataTable, close the modal
     * and reopen the previous Payments Modal
     */
    modalRequestApprovePayment.on('show.bs.modal', (event) => {
        const button = $(event.relatedTarget);
        const url = button.data('action');
        const form = modalRequestApprovePayment.find('form');
        const csrfMiddlewareToken = form.find('input[name="csrfmiddlewaretoken"]').val();

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
                        _reloadPaymentsDataTable();
                    }
                })
                .catch((error) => {
                    console.error(`Error posting approve request: ${error.message}`);
                });
            modalRequestApprovePayment.modal('hide');
        });
    })
        .on('hide.bs.modal', () => {
            modalRequestApprovePayment.find('textarea[name="comment"]').val('');
            modalRequestApprovePayment.find('#modal-button-confirm-accept-request').unbind('click');
        });



    /**
     * Table :: Payments :: Reject Button Click Handler
     * Open Reject Payment Modal
     * On Confirmation send a request to the API Endpoint, reload the Payments DataTable, close the modal
     * and reopen the previous Payments Modal
     */
    const modalRequestRejectDeclineError = modalRequestRejectPayment.find('#request-required-field');
    modalRequestRejectPayment.on('show.bs.modal', (event) => {
        const button = $(event.relatedTarget);
        const url = button.data('action');
        const form = modalRequestRejectPayment.find('form');
        const csrfMiddlewareToken = form.find('input[name="csrfmiddlewaretoken"]').val();

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
                            _reloadPaymentsDataTable();
                        }
                    })
                    .catch((error) => {
                        console.error(`Error posting delete request: ${error.message}`);
                    });
            }
        });
    })
        .on('hide.bs.modal', () => {
            modalRequestRejectPayment.find('textarea[name="comment"]').val('');
            modalRequestRejectDeclineError.addClass('d-none');
            modalRequestRejectPayment.find('#modal-button-confirm-accept-request').unbind('click');
        });

    /**
     * Table :: Payments :: Undo Button Click Handler
     * Open Undo Payment Modal
     * On Confirmation send a request to the API Endpoint, reload the Payments DataTable, close the modal
     * and reopen the previous Payments Modal
     */
    const modalRequestUndoDeclineError = modalRequestUndoPayment.find('#request-required-field');
    modalRequestUndoPayment.on('show.bs.modal', (event) => {
        const button = $(event.relatedTarget);
        const url = button.data('action');
        const form = modalRequestUndoPayment.find('form');
        const csrfMiddlewareToken = form.find('input[name="csrfmiddlewaretoken"]').val();

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
                            _reloadPaymentsDataTable();
                        }
                    })
                    .catch((error) => {
                        console.error(`Error posting delete request: ${error.message}`);
                    });
            }
        });
    })
        .on('hide.bs.modal', () => {
            modalRequestUndoPayment.find('textarea[name="comment"]').val('');
            modalRequestUndoDeclineError.addClass('d-none');
            modalRequestUndoPayment.find('#modal-button-confirm-accept-request').unbind('click');
        });

    /**
     * Table :: Payments :: Delete Button Click Handler
     * Open Delete Payment Modal
     * On Confirmation send a request to the API Endpoint, reload the Payments DataTable, close the modal
     * and reopen the previous Payments Modal
     */
    const modalRequestDeleteDeclineError = modalRequestDeletePayment.find('#request-required-field');
    modalRequestDeletePayment.on('show.bs.modal', (event) => {
        const button = $(event.relatedTarget);
        const url = button.data('action');
        const form = modalRequestDeletePayment.find('form');
        const csrfMiddlewareToken = form.find('input[name="csrfmiddlewaretoken"]').val();

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
                            _reloadPaymentsDataTable();
                        }
                    })
                    .catch((error) => {
                        console.error(`Error posting delete request: ${error.message}`);
                    });
            }
        });
    })
        .on('hide.bs.modal', () => {
            modalRequestDeletePayment.find('textarea[name="comment"]').val('');
            modalRequestDeleteDeclineError.addClass('d-none');
            modalRequestDeletePayment.find('#modal-button-confirm-accept-request').unbind('click');
        });


    /**
     * Table :: Payments :: Bulk Actions :: Update Bulk State
     * Updates the bulk action panel based on the number of selected checkboxes
     */
    const _updateBulkState = () => {
        const count = $(paymentsTable).find('.tax-row-select:checked').length;
        $('#tax-bulk-count').text(count);
        if (count > 0) {
            $('#tax-bulk-panel').removeClass('d-none').addClass('show');
        } else {
            $('#tax-bulk-panel').removeClass('show').addClass('d-none');
        }
    };
    /**
     * Table :: Payments :: Bulk Actions :: Reset States
     * Resets the bulk action panel and unchecks all selected checkboxes
     */
    const _resetBulkState = () => {
        $(paymentsTable).find('.tax-row-select').prop('checked', false);
        $('#tax-bulk-panel').addClass('d-none').removeClass('show');
    };

    /**
     * Table :: Payments :: Bulk Actions :: Clear Selection Button Click Handler
     * Resets the bulk action panel and unchecks all selected checkboxes
     */
    $('#tax-bulk-action-clear-selection').on('click', () => {
        _resetBulkState();
    });

    /**
     * Table :: Payments :: Bulk Actions :: Approve Button Click Handler
     * Open Approve Bulk Action Modal
     * On Confirmation send a request to the API Endpoint, reload the Payments DataTable, close the modal
     */
    modalRequestAcceptBulkActions.on('show.bs.modal', (event) => {
        const button = $(event.relatedTarget);
        const action = button.data('bulk-action');
        const selectedRows = $(paymentsTable).find('.tax-row-select:checked').closest('tr');
        const pks = selectedRows.map(function () {
            return $(this).find('.tax-row-select').data('payment-pk');
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
                        _resetBulkState();
                        _reloadPaymentsDataTable();
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
});
