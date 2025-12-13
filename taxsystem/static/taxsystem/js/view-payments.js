/* global aaTaxSystemSettings, aaTaxSystemSettingsOverride, _bootstrapTooltip, fetchGet, fetchPost, DataTable, numberFormatter */

$(document).ready(() => {
    // Table :: ID
    const paymentsTable = $('#payments');
    // Sub Modal :: Payments Details :: Tables
    const paymentInformationTable = $('#payment-information-table');
    const paymentDashboardTable = $('#payment-dashboard-table');
    const paymentHistoryTable = $('#payment-history-table');
    // Modal :: Payments Details
    const modalRequestViewPaymentsDetails = $('#taxsystem-view-payment-details');

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
                    filterDropDown: {
                        columns: [
                            {
                                idx: 1,
                                maxWidth: '200px',
                            },
                            {
                                idx: 4,
                                maxWidth: '200px',
                            },
                        ],
                        autoSize: false,
                        bootstrap: true,
                        bootstrap_version: 5
                    },
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
                    drawCallback: function () {
                        _bootstrapTooltip({selector: '#payments'});
                    }
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
        paymentDashboardTable.find('#payment-account').html(`${data.account.character.character_portrait} ${data.account.character.character_name}`);
        paymentDashboardTable.find('#payment-account-status').html(data.account.account_status);
        paymentDashboardTable.find('#payment-account-deposit').text(
            numberFormatter({
                value: data.account.payment_pool,
                language: aaTaxSystemSettings.locale,
                options: {
                    style: 'currency',
                    currency: 'ISK'
                }
            })
        );
        paymentDashboardTable.find('#payment-account-owner').text(data.owner.owner_name);
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
        paymentDashboardTable.find('#payment-account').html('N/A');
        paymentDashboardTable.find('#payment-account-status').html('N/A');
        paymentDashboardTable.find('#payment-account-deposit').text('N/A');
        paymentDashboardTable.find('#payment-account-owner').text('N/A');
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
});
