/* global taxsystemsettings */

$(document).ready(() => {
    const membersTableVar = $('#members');

    const tableMembers = membersTableVar.DataTable({
        ajax: {
            url: taxsystemsettings.corporationMembersUrl,
            type: 'GET',
            dataSrc: function (data) {
                return Object.values(data[0].corporation);
            },
        },
        columns: [
            {
                data: 'character_portrait',
                render: function (data, _, __) {
                    return data;
                }
            },
            {
                data: 'character_name',
                render: function (data, _, __) {
                    return data;
                }
            },
            {
                data: 'status',
                render: function (data, _, __) {
                    return data;
                }
            },
            {
                data: 'actions',
                render: function (data, _, __) {
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
        rowCallback: function(row, data) {
            if (data.is_faulty) {
                $(row).css('background-color', 'rgba(255, 0, 0, 0.1)');
            }
        },
    });


    tableMembers.on('draw', function () {
        $('[data-tooltip-toggle="taxsystem-tooltip"]').tooltip({
            trigger: 'hover',
        });
    });

    tableMembers.on('init.dt', function () {
        membersTableVar.removeClass('d-none');
    });
});
