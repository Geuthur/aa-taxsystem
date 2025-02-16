/* global taxsystemsettings bootstrap */

$(document).ready(() => {
    const ownpaymentsTableVar = $('#own-payments');

    const tableOwnPayments = ownpaymentsTableVar.DataTable({
        ajax: {
            url: taxsystemsettings.corporationOwnPaymentsUrl,
            type: 'GET',
            dataSrc: function (data) {
                return Object.values(data[0].corporation);
            },
            error: function (xhr, error, thrown) {
                console.error('Error loading data:', error);
                tableOwnPayments.clear().draw();
            }
        },
        stateSave: true, // Enable state saving
        columns: [
            {
                data: 'amount',
                render: function (data, type, row) {
                    const amount = parseFloat(data);
                    if (type === 'display') {
                        return amount.toLocaleString('de-DE') + ' ISK';
                    }
                    return amount;
                }
            },
            {
                data: 'date',
                render: function (data, _, row) {
                    return data;
                }
            },
            {
                data: 'request_status',
                render: function (data, _, row) {
                    return data;
                }
            },
            {
                data: 'reason',
                render: function (data, _, row) {
                    return data;
                }
            },
            {
                data: 'actions',
                render: function (data, _, row) {
                    return data;
                }
            },
        ],
        order: [[1, 'asc']],
        columnDefs: [
            { orderable: false, targets: [0, 2] },
        ],
        filterDropDown: {
            columns: [
                {
                    idx: 2,
                    maxWidth: '200px',
                },
            ],
            autoSize: false,
            bootstrap: true,
            bootstrap_version: 5
        },
    });

    tableOwnPayments.on('draw', function (row, data) {
        $('[data-tooltip-toggle="taxsystem-tooltip"]').tooltip({
            trigger: 'hover',
        });
    });
});
