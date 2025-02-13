/* global taxsystemsettings, bootstrap */
$(document).ready(function() {
    const entityPk = taxsystemsettings.entity_pk;

    // Dashboard-Info
    const manageDashboardVar = $('#dashboard-card');
    const manageDashboardTableVar = $('#manage-dashboard');
    // Dashboard-Divison
    const manageDashboardDivisionVar = $('#dashboard-division-card');
    const manageDashboardDivisionTableVar = $('#manage-dashboard-division');
    // Dashboard-Statistics
    const manageDashboardStatisticsVar = $('#dashboard-statistics-card');
    const manageDashboardStatisticsTableVar = $('#manage-dashboard-statistics');
    // Dashboard-Statistics-Payment System
    const manageDashboardStatisticsPaymentUsersVar = $('#dashboard-psystem-card');
    const manageDashboardStatisticsPaymentUsersTableVar = $('#manage-dashboard-psystem');

    $.ajax({
        url: taxsystemsettings.corporationmanageDashboardUrl,
        type: 'GET',
        success: function (data) {
            var tax_amount = parseFloat(data.tax_amount);
            var days = parseFloat(data.tax_period);
            $('#dashboard-info').html(data.corporation_name);
            $('#last_update_wallet').text(data.last_update_wallet);
            $('#last_update_members').text(data.last_update_members);
            $('#last_update_payments').text(data.last_update_payments);
            $('#last_update_paymentsystem').text(data.last_update_payment_system);
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

            manageDashboardVar.removeClass('d-none');
            manageDashboardTableVar.removeClass('d-none');

            // Show Divisions
            const divisions = data.divisions;
            const divisionKeys = Object.keys(divisions);

            for (let i = 0; i < divisionKeys.length; i++) {
                const divisionKey = divisionKeys[i];
                const division = divisions[divisionKey];

                try {
                    if (division && division.name && division.balance) {
                        $(`#division${i + 1}_name`).text(division.name);
                        $(`#division${i + 1}`).text(division.balance + ' ISK');
                    } else {
                        $(`#division${i + 1}_name`).hide();
                        $(`#division${i + 1}`).hide();
                    }
                } catch (e) {
                    console.error(`Error fetching division data for division ${i + 1}:`, e);
                    $(`#division${i + 1}_name`).hide();
                    $(`#division${i + 1}`).hide();
                }
            }

            manageDashboardDivisionVar.removeClass('d-none');
            manageDashboardDivisionTableVar.removeClass('d-none');

            // Statistics
            const statistics = data.statistics;
            const statisticsKey = Object.keys(statistics)[0];
            const stat = statistics[statisticsKey];

            try {
                if (stat) {
                    $('#statistics_name').text(statisticsKey);
                    $('#statistics_payments').text(stat.payments);
                    $('#statistics_payments_pending').text(stat.payments_pending);
                    $('#statistics_payments_auto').text(stat.payments_auto);
                    $('#statistics_payments_manually').text(stat.payments_manually);
                    // Members
                    $('#statistics_members').text(stat.members);
                    $('#statistics_members_mains').text(stat.members_mains);
                    $('#statistics_members_alts').text(stat.members_alts);
                    $('#statistics_members_not_registered').text(stat.members_unregistered);
                    // Payment Users
                    $('#statistics_payment_users').text(stat.payment_users);
                    $('#statistics_payment_users_active').text(stat.payment_users_active);
                    $('#statistics_payment_users_inactive').text(stat.payment_users_inactive);
                    $('#statistics_payment_users_deactivated').text(stat.payment_users_deactivated);
                } else {
                    $('#statistics_name').hide();
                    $('#statistics_payments').hide();
                    $('#statistics_payments_pending').hide();
                    $('#statistics_payments_auto').hide();
                    $('#statistics_payments_manually').hide();
                    // Members
                    $('#statistics_members').hide();
                    $('#statistics_members_mains').hide();
                    $('#statistics_members_alts').hide();
                    $('#statistics_members_not_registered').hide();
                    // Payment Users
                    $('#statistics_payment_users').hide();
                    $('#statistics_payment_users_active').hide();
                    $('#statistics_payment_users_inactive').hide();
                    $('#statistics_payment_users_deactivated').hide();
                }
            } catch (e) {
                console.error('Error fetching statistics data:', e);
                $('#statistics_name').hide();
                $('#statistics_payments').hide();
                $('#statistics_payments_pending').hide();
                $('#statistics_payments_auto').hide();
                $('#statistics_payments_manually').hide();
                // Members
                $('#statistics_members').hide();
                $('#statistics_members_mains').hide();
                $('#statistics_members_alts').hide();
                $('#statistics_members_not_registered').hide();
                // Payment Users
                $('#statistics_payment_users').hide();
                $('#statistics_payment_users_active').hide();
                $('#statistics_payment_users_inactive').hide();
                $('#statistics_payment_users_deactivated').hide();
            }

            manageDashboardStatisticsVar.removeClass('d-none');
            manageDashboardStatisticsTableVar.removeClass('d-none');
            manageDashboardStatisticsPaymentUsersVar.removeClass('d-none');
            manageDashboardStatisticsPaymentUsersTableVar.removeClass('d-none');

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
                data: 'status',
                render: function (data, _, row) {
                    return data;
                }
            },
            {
                data: 'wallet',
                render: function (data, type, row) {
                    const amount = parseFloat(data);
                    if (type === 'display') {
                        const viewPaymentUrl = `/taxsystem/api/corporation/${entityPk}/character/${row.character_id}/view/payments/`;
                        const button = `
                            <button type="button"
                                class="btn btn-sm btn-primary"
                                title="View Payments"
                                data-tooltip-toggle="taxsystem-tooltip"
                                data-bs-toggle="modal"
                                data-bs-target="#modalViewPaymentsContainer"
                                data-ajax_payments="${viewPaymentUrl}">
                            <span class="fas fa-info"></span></button>
                        `;

                        return amount.toLocaleString('de-DE') + ' ISK ' + button;
                    }
                    return amount;
                }
            },
            {
                data: 'has_paid',
                render: {
                    display: 'display',
                    _: 'sort'
                },
            },
            {
                data: 'last_paid',
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
            // Hidden columns
            {
                data: 'has_paid_filter',
            },
        ],
        order: [[1, 'asc']],
        columnDefs: [
            {
                orderable: false,
                targets: [0, 4]
            },
            // Filter Has Paid column
            {
                visible: false,
                targets: [7]
            },
        ],
        filterDropDown: {
            columns: [
                {
                    idx: 2,
                    maxWidth: '200px',
                },
                // has_paid
                {
                    idx: 7,
                    maxWidth: '200px',
                    title: taxsystemsettings.translations.hasPaid,
                },
            ],
            autoSize: false,
            bootstrap: true,
            bootstrap_version: 5
        },
        rowCallback: function(row, data) {
            if (!data.is_active) {
                $(row).css('background-color', 'rgba(255, 238, 0, 0.1)');
            } else if (data.is_active && data.has_paid.raw) {
                $(row).css('background-color', 'rgba(0, 255, 42, 0.1)');
            } else if (data.is_active && !data.has_paid.raw) {
                $(row).css('background-color', 'rgba(255, 0, 0, 0.1)');
            }
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
