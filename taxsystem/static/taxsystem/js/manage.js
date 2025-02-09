/* global taxsystemsettings */
$(document).ready(function() {
    const manageDashboardTableVar = $('#manage-dashboard');

    $.ajax({
        url: taxsystemsettings.corporationmanageDashboardUrl,
        type: 'GET',
        success: function (data) {
            var tax_amount = parseFloat(data.tax_amount);
            var days = parseFloat(data.tax_period);
            $('#dashboard-info').html(data.corporation_logo + ' ' + data.corporation_name);
            $('#last_update_wallet').text(data.last_update_wallet);
            $('#last_update_members').text(data.last_update_members);
            $('#last_update_payments').text(data.last_update_payments);
            $('#last_update_paymentsystem').text(data.last_update_filters);
            $('#taxamount').text(tax_amount);
            $('#period').text(days);

            // Generate URLs dynamically
            const updateTaxAmountUrl = taxsystemsettings.corporationUpdateTaxUrl;
            const updateTaxPeriodUrl = taxsystemsettings.corporationUpdatePeriodUrl;

            // Set data-url attributes dynamically
            $('#taxamount').attr('data-url', updateTaxAmountUrl);
            $('#period').attr('data-url', updateTaxPeriodUrl);

            // Initialize x-editable
            $('#taxamount').editable({
                type: 'text',
                pk: data.corporation_id,
                url: updateTaxAmountUrl,
                title: taxsystemsettings.translations.enterTaxAmount,
                display: function(value) {
                    // Parse the value to a number if it is not already
                    if (typeof value !== 'number') {
                        value = parseFloat(value);
                    }
                    // Display the value in the table with thousand separators
                    $(this).text(value.toLocaleString('de-DE') + ' ISK');
                },
                success: function(response, newValue) {
                    tablePaymentSystem.ajax.reload();
                },
                error: function(response, newValue) {
                    // Display an error message
                    if (response.status === 500) {
                        return taxsystemsettings.translations.internalServerError;
                    }
                    return response.responseJSON.message;
                }
            });

            $('#period').editable({
                type: 'text',
                pk: data.corporation_id,
                url: updateTaxPeriodUrl,
                title: taxsystemsettings.translations.enterTaxPeriod,
                display: function(value) {
                    // Parse the value to a number if it is not already
                    if (typeof value !== 'number') {
                        value = parseFloat(value);
                    }
                    // Display the value in the table with thousand separators
                    $(this).text(value.toLocaleString('de-DE') + ' ' + taxsystemsettings.translations.days);
                },
                success: function(response, newValue) {
                    tablePaymentSystem.ajax.reload();
                },
                error: function(response, newValue) {
                    // Display an error message
                    if (response.status === 500) {
                        return taxsystemsettings.translations.internalServerError;
                    }
                    return response.responseJSON.message;
                }
            });

            $('#taxamount').on('shown', function(e, editable) {
                // Display tax amount without formatting in the editable field
                editable.input.$input.val(editable.value.replace(/\./g, '').replace(' ISK', ''));
            });

            $('#period').on('shown', function(e, editable) {
                // Display tax period without formatting in the editable field
                editable.input.$input.val(editable.value.replace(' days', ''));
            });

            manageDashboardTableVar.removeClass('d-none');
        },
        error: function(xhr, status, error) {
            console.error('Error fetching data:', error);
        }
    });

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
                data: 'joined',
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

    const PaymentSystemTableVar = $('#payment-system');

    const tablePaymentSystem = PaymentSystemTableVar.DataTable({
        ajax: {
            url: taxsystemsettings.corporationPaymentSystemUrl,
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
                    const amount = parseFloat(data);
                    return amount.toLocaleString('de-DE') + ' ISK';
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

    tablePaymentSystem.on('init.dt', function () {
        PaymentSystemTableVar.removeClass('d-none');
    });

    tablePaymentSystem.on('draw', function (row, data) {
        $('[data-tooltip-toggle="taxsystem-tooltip"]').tooltip({
            trigger: 'hover',
        });
    });
});
