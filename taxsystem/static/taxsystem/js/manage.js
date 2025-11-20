/* global taxsystemsettings, bootstrap, moment, numberFormatter */
$(document).ready(function() {
    const entityPk = taxsystemsettings.entity_pk;

    // Dashboard-Info
    const manageDashboardVar = $('#dashboard-card');
    const manageDashboardTableVar = $('#manage-dashboard');
    // Dashboard-Update Status
    const manageUpdateStatusVar = $('#update-status-card');
    const manageUpdateStatusTableVar = $('#manage-update-dashboard');
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
        url: taxsystemsettings.DashboardUrl,
        type: 'GET',
        success: function (data) {
            var tax_amount = parseFloat(data.tax_amount);
            var days = parseFloat(data.tax_period);
            $('#dashboard-info').html(data.corporation.corporation_name);

            $('#dashboard-update').html(data.corporation.corporation_name + ' - Update Status');
            // Use moment.js to display relative times in German
            $('#update_status_icon').html(data.update_status.icon);
            $('#update_wallet').html(data.update_status.status.wallet && data.update_status.status.wallet.last_run_finished_at
                ? moment(data.update_status.status.wallet.last_run_finished_at).fromNow()
                : 'N/A');
            $('#update_division').html(data.update_status.status.division && data.update_status.status.division.last_run_finished_at
                ? moment(data.update_status.status.division.last_run_finished_at).fromNow()
                : 'N/A');
            $('#update_division_name').html(data.update_status.status.division_names && data.update_status.status.division_names.last_run_finished_at
                ? moment(data.update_status.status.division_names.last_run_finished_at).fromNow()
                : 'N/A');
            $('#update_members').html(data.update_status.status.members && data.update_status.status.members.last_run_finished_at
                ? moment(data.update_status.status.members.last_run_finished_at).fromNow()
                : 'N/A');
            $('#update_payments').html(data.update_status.status.payments && data.update_status.status.payments.last_run_finished_at
                ? moment(data.update_status.status.payments.last_run_finished_at).fromNow()
                : 'N/A');
            $('#update_payment_system').html(data.update_status.status.payment_system && data.update_status.status.payment_system.last_run_finished_at
                ? moment(data.update_status.status.payment_system.last_run_finished_at).fromNow()
                : 'N/A');

            $('#taxamount').text(tax_amount);
            $('#period').text(days);
            $('#activity').html(data.activity);

            // Generate URLs dynamically
            const updateTaxAmountUrl = taxsystemsettings.UpdateTaxUrl;
            const updateTaxPeriodUrl = taxsystemsettings.UpdatePeriodUrl;

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
                success: function() {
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
                success: function() {
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

            // Update Status
            manageUpdateStatusVar.removeClass('d-none');
            manageUpdateStatusTableVar.removeClass('d-none');

            // Show Divisions
            const divisionsData = data.divisions;
            const divisions = divisionsData.divisions; // Das Array mit den Divisionen

            if (!divisions || divisions.length === 0) {
                // Wenn divisions leer ist, zeige N/A nur für die Division-Nummern
                for (let i = 1; i <= 7; i++) {
                    $(`#division${i}_name`).show(); // Name bleibt wie er ist
                    $(`#division${i}`).text('N/A').show();
                }
            } else {
                for (let i = 0; i < divisions.length; i++) {
                    const division = divisions[i];
                    try {
                        if (division && division.name && division.balance) {
                            $(`#division${i + 1}_name`).text(division.name);
                            $(`#division${i + 1}`).text(
                                numberFormatter({
                                    value: division.balance,
                                    options: {
                                        style: 'currency',
                                        currency: 'ISK'
                                    }
                                })
                            );
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
            }

            // Gesamtbilanz anzeigen
            if (!divisions || divisions.length === 0) {
                $('#total_balance').text('N/A');
            } else {
                $('#total_balance').text(
                    numberFormatter({
                        value: divisionsData.total_balance,
                        options: {
                            style: 'currency',
                            currency: 'ISK'
                        }
                    })
                );
            }

            manageDashboardDivisionVar.removeClass('d-none');
            manageDashboardDivisionTableVar.removeClass('d-none');

            // Statistics
            const statistics = data.statistics;

            try {
                $('#statistics_payment_users').text(statistics.payment_system.ps_count);
                $('#statistics_payment_users_active').text(statistics.payment_system.ps_count_active);
                $('#statistics_payment_users_inactive').text(statistics.payment_system.ps_count_inactive);
                $('#statistics_payment_users_deactivated').text(statistics.payment_system.ps_count_deactivated);
                $('#psystem_payment_users_paid').text(statistics.payment_system.ps_count_paid);
                $('#psystem_payment_users_unpaid').text(statistics.payment_system.ps_count_unpaid);

                // Payments
                $('#statistics_payments').text(statistics.payments.payments_count);
                $('#statistics_payments_pending').text(statistics.payments.payments_pending);
                $('#statistics_payments_auto').text(statistics.payments.payments_automatic);
                $('#statistics_payments_manually').text(statistics.payments.payments_manual);

                // Members
                $('#statistics_members').text(statistics.members.members_count);
                $('#statistics_members_mains').text(statistics.members.members_mains);
                $('#statistics_members_alts').text(statistics.members.members_alts);
                $('#statistics_members_not_registered').text(statistics.members.members_unregistered);
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
                $('#psystem_payment_users_paid').hide();
                $('#psystem_payment_users_unpaid').hide();
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
            url: taxsystemsettings.MembersUrl,
            type: 'GET',
            dataSrc: function (data) {
                return data.corporation;
            },
            error: function (xhr, error, thrown) {
                console.error('Error loading data:', error);
                tableMembers.clear().draw();
            }
        },
        columns: [
            {
                data: 'character.character_portrait',
                render: function (data, _, __) {
                    return data;
                }
            },
            {
                data: 'character.character_name',
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
                    const date = moment(data);
                    if (!data || !date.isValid()) {
                        return 'N/A';
                    }
                    return date.fromNow();
                }
            },
            {
                data: 'actions',
                render: function (data, _, __) {
                    return data;
                }
            },
        ],
        order: [[3, 'desc']],
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
                $(row).addClass('tax-red tax-hover');
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
            url: taxsystemsettings.PaymentSystemUrl,
            type: 'GET',
            dataSrc: function (data) {

                return data.corporation;
            },
            error: function (xhr, error, thrown) {
                console.error('Error loading data:', error);
                tablePaymentSystem.clear().draw();
            }
        },
        columns: [
            {
                data: 'account.character_portrait',
                render: function (data, _, row) {
                    return data;
                }
            },
            {
                data: 'account.character_name',
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
                data: 'deposit',
                render: {
                    display: function (data, _, row) {
                        return numberFormatter({
                            value: data,
                            options: {
                                style: 'currency',
                                currency: 'ISK'
                            }
                        });
                    },
                    filter: function (data, _, row) {
                        return data;
                    },
                    _: function (data, _, row) {
                        return data;
                    }
                },
                className: 'text-end'
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
                    const date = moment(data);
                    if (!data || !date.isValid()) {
                        return 'N/A';
                    }
                    return date.format('YYYY-MM-DD HH:mm:ss');
                }
            },
            {
                data: 'actions',
                render: function (data, _, row) {
                    return data;
                },
                className: 'text-end'
            },
            // Hidden columns
            {
                data: 'has_paid.dropdown_text',
            },
        ],
        order: [[1, 'asc']],
        columnDefs: [
            {
                orderable: false,
                targets: [0, 4, 6]
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
                $(row).addClass('tax-warning tax-hover');
            } else if (data.is_active && data.has_paid.raw) {
                $(row).addClass('tax-green tax-hover');
            } else if (data.is_active && !data.has_paid.raw) {
                $(row).addClass('tax-red tax-hover');
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
