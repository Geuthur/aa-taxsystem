/* global taxsystemsettings bootstrap */

$(document).ready(() => {
    const paymentsTableVar = $('#payments');

    const tablePayments = paymentsTableVar.DataTable({
        ajax: {
            url: taxsystemsettings.corporationPaymentsUrl,
            type: 'GET',
            dataSrc: function (data) {
                return Object.values(data[0].corporation);
            },
            error: function (xhr, error, thrown) {
                console.error('Error loading data:', error);
                tablePayments.clear().draw();
            }
        },
        stateSave: true, // Enable state saving
        columns: [
            {
                data: 'character_portrait',
                render: function (data, _, row) {
                    return data;
                }
            },
            {
                data: 'character_name',
                render: function (data, _, row) {
                    return data;
                }
            },
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
    });

    tablePayments.on('draw', function (row, data) {
        $('[data-tooltip-toggle="taxsystem-tooltip"]').tooltip({
            trigger: 'hover',
        });
    });
});
