/* global taxsystemsettings */

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
                data: 'payment_date',
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
