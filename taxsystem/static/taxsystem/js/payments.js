/* global taxsystemsettings bootstrap */

$(document).ready(() => {
    const adminstationTableVar = $('#payments');

    const tablePayments = adminstationTableVar.DataTable({
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
                render: function (data, _, row) {
                    const amount = parseFloat(data);
                    return amount.toLocaleString('de-DE') + ' ISK';
                }
            },
            {
                data: 'payment_date',
                render: function (data, _, row) {
                    return data;
                }
            },
            {
                data: 'status',
                render: function (data, _, row) {
                    return data;
                }
            },
            {
                data: 'approved',
                render: function (data, _, row) {
                    return data;
                }
            },
            {
                data: 'system',
                render: function (data, _, row) {
                    return data;
                }
            },
            {
                data: 'reason',
                render: function (data, _, row) {
                    return data;
                },
                className: 'ts-reason'
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

    tablePayments.on('init.dt', function () {
        adminstationTableVar.removeClass('d-none');
    });

    tablePayments.on('draw', function (row, data) {
        $('[data-tooltip-toggle="taxsystem-tooltip"]').tooltip({
            trigger: 'hover',
        });
    });
});
