/* global aaTaxSystemSettings, aaTaxSystemSettingsOverride, _bootstrapTooltip, fetchGet, fetchPost, DataTable, numberFormatter */

$(document).ready(() => {
    /**
     * Table :: IDs
     */
    const AdminHistoryTable = $('#admin-history-table');

    /**
     * Table :: Admin History
     * Initialize DataTable with Ajax Data
     * @type {*|jQuery}
     */
    fetchGet({url: aaTaxSystemSettings.url.AdminHistory})
        .then((data) => {
            if (data) {
                const filterSetDataTable = new DataTable(AdminHistoryTable, {
                    data: data,
                    language: aaTaxSystemSettings.dataTables.language,
                    layout: aaTaxSystemSettings.dataTables.layout,
                    ordering: aaTaxSystemSettings.dataTables.ordering,
                    columnControl: aaTaxSystemSettings.dataTables.columnControl,
                    order: [[0, 'desc']],
                    pageLength: 25,
                    columns: [
                        { data: 'log_id' },
                        { data: 'user_name'},
                        { data: 'date'},
                        { data: 'target'},
                        {
                            data: {
                                display: (data) => data.action.display,
                                sort: (data) => data.action.sort,
                                filter: (data) => data.action.sort
                            }
                        },
                        { data: 'comment' },
                    ],
                    columnDefs: [
                        {
                            targets: [0],
                            orderable: false,
                            columnControl: [
                                {target: 0, content: []},
                                {target: 1, content: []}
                            ]
                        },
                    ],
                    initComplete: function () {
                        _bootstrapTooltip({selector: '#admin-history-table'});


                    },
                    drawCallback: function () {
                        _bootstrapTooltip({selector: '#admin-history-table'});
                    },
                    rowCallback: function(row, data) {
                        if (data.action.raw === 'Deleted') {
                            $(row).addClass('tax-red tax-hover');
                        }
                        if (data.action.raw === 'Changed') {
                            $(row).addClass('tax-blue tax-hover');
                        }
                        if (data.action.raw === 'Added') {
                            $(row).addClass('tax-green tax-hover');
                        }
                    },
                });
            }
        })
        .catch((error) => {
            console.error(`Error fetching Filter-Set DataTable: ${error.message}`);
        });
});
