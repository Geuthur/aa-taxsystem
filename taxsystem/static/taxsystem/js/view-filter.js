/* global aaTaxSystemSettings, aaTaxSystemSettingsOverride, _bootstrapTooltip, fetchGet, fetchPost, DataTable, numberFormatter */

$(document).ready(() => {
    /**
     * Table :: IDs
     */
    const filterSetTable = $('#filter-sets-table');
    const filterTable = $('#filter-table');

    /**
     * Modal :: IDs
     */
    const modalRequestDeleteFilterSet = $('#taxsystem-accept-delete-filter-set');
    const modalRequestDeleteFilter = $('#taxsystem-accept-delete-filter');
    const modalRequestViewFilterSet = $('#taxsystem-view-filter-set');

    /**
     * Table :: Filter-Set :: Reload Filter DataTable
     * Handle Reloading of Filter-Set DataTable with new Data from API
     * @param {Object} tableData # Ajax API Response Data
     * @private
     */
    const _reloadFilterDataTable = (tableData) => {
        const dtActive = filterSetTable.DataTable();
        dtActive.clear().rows.add(tableData).draw();
    };

    /**
     * Table :: Filter-Set :: Switch Button Click Handler
     * Handle Click Event for Switch Filter-Set Button in Filter-Set Table, which sends Post Request to Switch Filter-Set API Endpoint
     * On Success, Reload Filter-Set DataTable with new Data from API
     * @private
     */
    const switchFilterSetSelector = '#taxsystem-switch-filter-set-button';
    filterSetTable.on('click', switchFilterSetSelector, function (event) {
        const button = $(event.currentTarget || this);
        const url = button.data('action');

        if (!url) {
            console.error('No data-action URL found on switch button');
            return;
        }

        fetchPost({
            url: url,
            csrfToken: aaTaxSystemSettings.csrfToken,
        })
            .then((data) => {
                if (data && data.success === true) {
                    fetchGet({ url: aaTaxSystemSettings.url.FilterSet })
                        .then((newData) => {
                            _reloadFilterDataTable(newData);
                        })
                        .catch((error) => {
                            console.error('Error fetching Filter-Set DataTable after switch:', error);
                        });
                }
            })
            .catch((error) => {
                console.error(`Error posting switching request: ${error.message}`);
            });
    });

    /**
     * Table :: Filter-Set
     * Initialize DataTable with Ajax Data
     * @type {*|jQuery}
     */
    fetchGet({url: aaTaxSystemSettings.url.FilterSet})
        .then((data) => {
            if (data) {
                const filterSetDataTable = new DataTable(filterSetTable, {
                    data: data,
                    language: aaTaxSystemSettings.dataTables.language,
                    layout: aaTaxSystemSettings.dataTables.layout,
                    ordering: aaTaxSystemSettings.dataTables.ordering,
                    columnControl: aaTaxSystemSettings.dataTables.columnControl,
                    order: [[0, 'desc']],
                    pageLength: 25,
                    columns: [
                        { data: 'name' },
                        { data: 'description'},
                        {
                            data: {
                                display: (data) => data.status.display,
                                sort: (data) => data.status.sort,
                                filter: (data) => data.status.sort
                            }
                        },
                        { data: 'actions'},
                    ],
                    columnDefs: [
                        {
                            targets: [2, 3],
                            orderable: false,
                            columnControl: [
                                {target: 0, content: []},
                                {target: 1, content: []}
                            ]
                        },
                    ],
                    initComplete: function () {
                        _bootstrapTooltip({selector: '#filter-sets-table'});
                    },
                    drawCallback: function () {
                        _bootstrapTooltip({selector: '#filter-sets-table'});
                    },
                });
            }
        })
        .catch((error) => {
            console.error(`Error fetching Filter-Set DataTable: ${error.message}`);
        });

    /**
     * Modal:: Filter-Set :: Helper Function :: Load Modal DataTable
     * Load data into Filter-Set Modal DataTable and redraw
     * @param {Object} tableData Ajax API Response Data
     * @private
     */
    const _loadFilterModalDataTable = (tableData) => {
        const dtFilterSet = filterTable.DataTable();
        dtFilterSet.clear().rows.add(tableData).draw();
    };

    /**
     * Modal:: Filter-Set :: Helper Function :: Clear Modal DataTable
     * Clear data from Filter-Set Modal DataTable and redraw
     * @private
     */
    const _clearFilterModalDataTable = () => {
        const dtFilterSet = filterTable.DataTable();
        dtFilterSet.clear().draw();
    };

    /**
     * Modal :: Filter-Set :: Table :: Filter
     * Initialize DataTable for Filter-Set Modal Filter Data
     * @type {*|jQuery}
     */
    const filterDataTable = new DataTable(filterTable, {
        data: null, // Loaded via API on modal open
        language: aaTaxSystemSettings.dataTables.language,
        layout: aaTaxSystemSettings.dataTables.layout,
        ordering: aaTaxSystemSettings.dataTables.ordering,
        columnControl: aaTaxSystemSettings.dataTables.columnControl,
        order: [[0, 'desc']],
        columns: [
            { data: 'filter_type' },
            {
                data: {
                    display: (data) => data.value.display,
                    sort: (data) => data.value.sort,
                    filter: (data) => data.value.sort
                }
            },
            { data: 'actions' },
        ],
        columnDefs: [
            {
                targets: [2],
                orderable: false,
                columnControl: [
                    {target: 0, content: []},
                    {target: 1, content: []}
                ]
            },
        ],
        initComplete: function () {
            _bootstrapTooltip({selector: '#filter-table'});
        },
        drawCallback: function () {
            _bootstrapTooltip({selector: '#filter-table'});
        },
    });

    /**
     * Modal :: Filter-Set :: Info Button Click Handler
     * @const {_loadFilterModalDataTable} :: Load Filter Data into Filter DataTable in the Filter-Set Modal
     * @const {_clearFilterModalDataTable} :: Clear Filter-Set DataTable in the Filter-Set Modal on Close
     * When opening, fetch data from the API Endpoint defined in the button's data-action attribute
     * and load it into the Filter-Set Modal DataTable
     */
    modalRequestViewFilterSet.on('show.bs.modal', (event) => {
        const button = $(event.relatedTarget);
        const url = button.data('action');

        // guard clause for previous Modal reload function
        if (!url) {
            return;
        }

        fetchGet({
            url: url,
        })
            .then((data) => {
                if (data) {
                    _loadFilterModalDataTable(data);
                }
            })
            .catch((error) => {
                console.error('Error fetching Filter Set Modal:', error);
            });
    })
        .on('hide.bs.modal', () => {
            _clearFilterModalDataTable();
        });

    /**
     * Modal :: Filter-Set :: Delete Button Click Handler
     * Open Filter-Set Delete Modal
     * When the send request to delete the filter-set is confirmed, reload the filter-set DataTable
     * and Close Modal
     */
    const modalRequestFilterSetDeclineError = modalRequestDeleteFilterSet.find('#request-required-field');
    modalRequestDeleteFilterSet.on('show.bs.modal', (event) => {
        const button = $(event.relatedTarget);
        const url = button.data('action');
        const form = modalRequestDeleteFilterSet.find('form');
        const csrfMiddlewareToken = form.find('input[name="csrfmiddlewaretoken"]').val();

        modalRequestDeleteFilterSet.find('#modal-button-confirm-accept-request').on('click', () => {
            const rejectInfo = form.find('textarea[name="comment"]');
            const rejectInfoValue = rejectInfo.val();

            if (rejectInfoValue === '') {
                modalRequestFilterSetDeclineError.removeClass('d-none');
                rejectInfo.addClass('is-invalid');

                // Add shake class to the error field
                rejectInfo.addClass('ts-shake');

                // Remove the shake class after 3 seconds
                setTimeout(() => {
                    rejectInfo.removeClass('ts-shake');
                    rejectInfo.removeClass('is-invalid');
                }, 1500);
            } else {
                fetchPost({
                    url: url,
                    csrfToken: csrfMiddlewareToken,
                    payload: {
                        comment: rejectInfoValue
                    }
                })
                    .then((data) => {
                        if (data.success === true) {
                            fetchGet({
                                url: aaTaxSystemSettings.url.FilterSet
                            })
                                .then((newData) => {
                                    _reloadFilterDataTable(newData);
                                })
                                .catch((error) => {
                                    console.error('Error fetching Filter-Set DataTable:', error);
                                });
                        }
                    })
                    .catch((error) => {
                        console.error(`Error posting delete request: ${error.message}`);
                    });
                modalRequestDeleteFilterSet.modal('hide');
            }
        });
    })
        .on('hide.bs.modal', () => {
            modalRequestFilterSetDeclineError.addClass('d-none');
            modalRequestDeleteFilterSet.find('#modal-button-confirm-accept-request').unbind('click');
        });

    /**
     * Sub Modal :: Filter :: Helper Function :: Load Previous Modal 'Filter-Set'
     * Load Previous Filter-Set Modal from API Endpoint URL
     * @param {string} apiUrl Previous Modal API Endpoint URL
     * @private
     */
    const _loadPreviousModal = (apiUrl) => {
        fetchGet({
            url: apiUrl
        })
            .then((newData) => {
                _loadFilterModalDataTable(newData);
                modalRequestViewFilterSet.modal('show');
            })
            .catch((error) => {
                console.error('Error fetching Filter-Set DataTable:', error);
            });
    };

    /**
     * Sub-Modal :: Filter :: Delete Button Click Handler
     * Open Filter Delete Modal from Previous opened Filter-Set Modal
     * When the send request to delete the filter is confirmed, reload the filter DataTable
     * and Close Modal, Reopen Previous Filter-Set Modal depending on 'previous-modal' data attribute
     */
    const modalRequestFilterDeclineError = modalRequestDeleteFilter.find('#request-required-field');
    modalRequestDeleteFilter.on('show.bs.modal', (event) => {
        const button = $(event.relatedTarget);
        const url = button.data('action');
        const previousUrl = button.data('previous-modal');
        // store previous modal url in modal data for later use
        modalRequestDeleteFilter.data('previous-modal', previousUrl);

        const form = modalRequestDeleteFilter.find('form');
        const csrfMiddlewareToken = form.find('input[name="csrfmiddlewaretoken"]').val();

        modalRequestDeleteFilter.find('#modal-button-confirm-accept-request').on('click', () => {
            const rejectInfo = form.find('textarea[name="comment"]');
            const rejectInfoValue = rejectInfo.val();

            if (rejectInfoValue === '') {
                modalRequestFilterDeclineError.removeClass('d-none');
                rejectInfo.addClass('is-invalid');

                // Add shake class to the error field
                rejectInfo.addClass('ts-shake');

                // Remove the shake class after 3 seconds
                setTimeout(() => {
                    rejectInfo.removeClass('ts-shake');
                    rejectInfo.removeClass('is-invalid');
                }, 1500);
            } else {
                fetchPost({
                    url: url,
                    csrfToken: csrfMiddlewareToken,
                    payload: {
                        comment: rejectInfoValue
                    }
                })
                    .then((data) => {
                        if (data.success === true) {
                            modalRequestDeleteFilter.modal('hide');
                        }
                    })
                    .catch((error) => {
                        console.error(`Error posting delete request: ${error.message}`);
                    });
            }
        });
    })
        .on('hide.bs.modal', (event) => {
        // get previous modal url from modal data
            const previousUrl = modalRequestDeleteFilter.data('previous-modal');
            modalRequestDeleteFilter.find('textarea[name="comment"]').val('');

            // load previous modal if apiUrl exists
            if (previousUrl) {
                _loadPreviousModal(previousUrl);
            }

            // reset state
            modalRequestFilterDeclineError.addClass('d-none');
            modalRequestDeleteFilter.find('#modal-button-confirm-accept-request').unbind('click');
        });
});
