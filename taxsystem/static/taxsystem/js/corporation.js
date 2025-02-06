/* global taxsystemsettings */

function initTooltip() {
    $('[data-tooltip-toggle="taxsystem-tooltip"]').tooltip({
        trigger: 'hover',
    });
    if (taxsystemsettings.entity_type !== 'character') {
        $('[data-bs-toggle="taxsystem-popover"]').popover({
            trigger: 'hover',
            html: true,
        });
    }
}

function generateTable(TableName, url) {
    var table = TableName;

    if (window[TableName]) {
        $('#members').DataTable().destroy();
    }

    $.ajax({
        url: url,
        type: 'GET',
        success: function(data) {
            var membersData = Object.values(data[0].corporation); // Extract the members data

            window[table] = $('#members').DataTable({
                data: membersData,
                columns: [
                    {
                        data: 'character_id',
                        render: function (data, _, row) {
                            var imageUrl = 'https://images.evetech.net/';
                            imageUrl += 'characters/' + data + '/portrait?size=32';

                            var imageHTML = '';
                            imageHTML += `
                            <img
                                src='${imageUrl}'
                                class="rounded-circle">
                            `;
                            return imageHTML;
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
                ],
                order: [[1, 'asc']],
                columnDefs: [
                    { orderable: false, targets: [0] },
                ],
                initComplete: function () {
                    $('#members').removeClass('d-none');
                    initTooltip();
                },
                drawCallback: function () {
                    initTooltip();
                },
            });
        },
        error: function(xhr, _, __) {
            var table = $('#members').DataTable();
            table.clear().draw(); // Clear the table

            var errorMessage = '';
            if (xhr.status === 403) {
                errorMessage = 'You have no permission to view this page';
            } else if (xhr.status === 404) {
                errorMessage = 'No data found';
            }

            if (errorMessage) {
                table.rows.add([
                    { character_id: '', character_name: errorMessage, status: '' }
                ]).draw();
                $('#members').removeClass('d-none');
            }
        }
    });
}

document.addEventListener('DOMContentLoaded', function () {
    generateTable('members', taxsystemsettings.corporationMembersUrl);
});
