/* global aaTaxSystemSettings, aaTaxSystemSettingsOverride, _bootstrapTooltip, fetchGet, fetchPost, DataTable, SlimSelect, numberFormatter */

$(document).ready(() => {
    // Table :: ID
    const paymentsTable = $('#my-payments');

    fetchGet({
        url: aaTaxSystemSettings.url.MyPayments
    })
        .then((data) => {
            if (data) {
            /**
             * Table :: Payments
             */
                const paymentsDataTable = new DataTable(paymentsTable, {
                    data: data,
                    language: aaTaxSystemSettings.dataTables.language,
                    layout: aaTaxSystemSettings.dataTables.layout,
                    ordering: aaTaxSystemSettings.dataTables.ordering,
                    columnControl: aaTaxSystemSettings.dataTables.columnControl,
                    order: [[1, 'desc']],
                    columnDefs: [
                        { targets: [0], type: 'num' },
                        { targets: [0], type: 'date' }
                    ],
                    columns: [
                        {
                            data: {
                                display: (data) => numberFormatter({
                                    value: data.amount,
                                    language: aaTaxSystemSettings.locale,
                                    options: {
                                        style: 'currency',
                                        currency: 'ISK'
                                    }
                                }),
                                sort: (data) => data.amount,
                                filter: (data) => data.amount
                            }
                        },
                        { data: 'date' },
                        { data: 'request_status.status' },
                    ],
                    drawCallback: function () {
                        _bootstrapTooltip({selector: '#payments'});
                    }
                });
            }
        })
        .catch((error) => {
            console.error('Error fetching Payments DataTable:', error);
        });
});
