/* global taxsystemsettings */

$(document).ready(() => {
    const adminstationTableVar = $('#administration');

    const tableAdministration = adminstationTableVar.DataTable({
        ajax: {
            url: taxsystemsettings.corporationAdministrationUrl,
            type: 'GET',
            dataSrc: function (data) {
                return Object.values(data[0].corporation);
            },
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
                data: 'status',
                render: function (data, _, row) {
                    return data;
                }
            },
            {
                data: 'wallet',
                render: function (data, _, row) {
                    return data;
                }
            },
            {
                data: 'has_paid',
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
                }
            ],
            autoSize: false,
            bootstrap: true,
            bootstrap_version: 5
        },
    });

    tableAdministration.on('init.dt', function () {
        adminstationTableVar.removeClass('d-none');
    });

    tableAdministration.on('draw', function (row, data) {
        $('[data-tooltip-toggle="taxsystem-tooltip"]').tooltip({
            trigger: 'hover',
        });
    });
});
