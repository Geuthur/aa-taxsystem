/* global aaTaxSystemSettings, aaTaxSystemSettingsOverride, _bootstrapTooltip, fetchGet, fetchPost, DataTable, numberFormatter */

$(document).ready(() => {
    /**
     * Table :: IDs
     */
    const groupsTable = $('#groups-table');

    /**
     * Modal :: IDs
     */
    const modalRequestDeleteGroup = $('#taxsystem-accept-delete-group');

    /**
     * Table :: Groups
     */
    const groupsDataTable = new DataTable(groupsTable, {
        data: [],
        language: aaTaxSystemSettings.dataTables.language,
        layout: aaTaxSystemSettings.dataTables.layout,
        ordering: aaTaxSystemSettings.dataTables.ordering,
        columnControl: aaTaxSystemSettings.dataTables.columnControl,
        order: [[0, 'desc']],
        columnDefs: [
            {
                orderable: false,
                targets:  [1, 2],
                columnControl: [
                    {target: 0, content: []},
                    {target: 1, content: []}
                ]
            },
        ],
        columns: [
            { data: 'name' },
            {
                data: {
                    display: (data) => data.groups.map((group) => group.name).join(', '),
                    sort: (data) => data.groups.map((group) => group.name).join(', '),
                    filter: (data) => data.groups.map((group) => group.name).join(', '),
                }
            },
            {
                data: {
                    display: (data) => data.actions,
                    sort: (data) => data.name,
                    filter: (data) => data.name,
                },
                className: 'text-end'
            },
        ],
        initComplete: function() {
            _bootstrapTooltip({selector: '#groups-table'});
        },
        drawCallback: function () {
            _bootstrapTooltip({selector: '#groups-table'});
        },
    });


    fetchGet({
        url: aaTaxSystemSettings.url.Groups
    })
        .then((data) => {
            groupsDataTable.clear().rows.add(data).draw();
        })
        .catch((error) => {
            console.error('Error fetching Groups DataTable:', error);
            groupsDataTable.clear().draw();
        });


    /**
     * Modal :: Group :: Delete Button Click Handler
     * Open Group Delete Modal
     * When the send request to delete the group is confirmed, reload the group DataTable
     * and Close Modal
     */
    const modalRequestGroupDeclineError = modalRequestDeleteGroup.find('#request-required-field');
    modalRequestDeleteGroup.on('show.bs.modal', (event) => {
        const button = $(event.relatedTarget);
        const url = button.data('action');
        const form = modalRequestDeleteGroup.find('form');
        const csrfMiddlewareToken = form.find('input[name="csrfmiddlewaretoken"]').val();

        modalRequestDeleteGroup.find('#modal-button-confirm-accept-request').on('click', () => {
            const deleteInfo = form.find('textarea[name="comment"]');
            const deleteInfoValue = deleteInfo.val();

            if (deleteInfoValue === '') {
                modalRequestGroupDeclineError.removeClass('d-none');
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
                            fetchGet({
                                url: aaTaxSystemSettings.url.Groups
                            })
                                .then((newData) => {
                                    groupsDataTable.clear().rows.add(newData).draw();
                                })
                                .catch((error) => {
                                    console.error('Error fetching Groups DataTable:', error);
                                });
                        }
                    })
                    .catch((error) => {
                        console.error(`Error posting delete request: ${error.message}`);
                    });
                modalRequestDeleteGroup.modal('hide');
            }
        });
    })
        .on('hide.bs.modal', () => {
            modalRequestGroupDeclineError.addClass('d-none');
            modalRequestDeleteGroup.find('#modal-button-confirm-accept-request').unbind('click');
        });
});
