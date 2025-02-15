$(document).ready(() => {
    /* global tablePayments */
    /* global taxsystemsettings */
    const modalRequestSwitchuser = $('#paymentsystem-switchuser');

    // Funktion zum Neuladen der Statistikdaten
    function reloadStatistics() {
        $.ajax({
            url: taxsystemsettings.corporationmanageDashboardUrl,
            type: 'GET',
            success: function (data) {
                // Statistics
                const statistics = data.statistics;
                const statisticsKey = Object.keys(statistics)[0];
                const stat = statistics[statisticsKey];

                $('#statistics_payment_users').text(stat.payment_users);
                $('#statistics_payment_users_active').text(stat.payment_users_active);
                $('#statistics_payment_users_inactive').text(stat.payment_users_inactive);
                $('#statistics_payment_users_deactivated').text(stat.payment_users_deactivated);
                $('#psystem_payment_users_paid').text(stat.payment_users_paid);
                $('#psystem_payment_users_unpaid').text(stat.payment_users_unpaid);
            },
            error: function(xhr, status, error) {
                console.error('Error fetching statistics data:', error);
            }
        });
    }

    // Switchuser Request Modal
    modalRequestSwitchuser.on('show.bs.modal', (event) => {
        const button = $(event.relatedTarget);
        const url = button.data('action');

        // Extract the title from the button
        const modalTitle = button.data('title');
        const modalTitleDiv = modalRequestSwitchuser.find('#modal-title');
        modalTitleDiv.html(modalTitle);

        // Extract the text from the button
        const modalText = button.data('text');
        const modalDiv = modalRequestSwitchuser.find('#modal-request-text');
        modalDiv.html(modalText);

        $('#modal-button-confirm-switchuser-request').on('click', () => {
            const form = modalRequestSwitchuser.find('form');
            const csrfMiddlewareToken = form.find('input[name="csrfmiddlewaretoken"]').val();

            const posting = $.post(
                url,
                {
                    csrfmiddlewaretoken: csrfMiddlewareToken
                }
            );

            posting.done((data) => {
                if (data.success === true) {
                    modalRequestSwitchuser.modal('hide');

                    const paymentsystemTable = $('#payment-system').DataTable();
                    paymentsystemTable.ajax.reload();

                    // Neuladen der Statistikdaten
                    reloadStatistics();
                }
            }).fail((xhr, _, __) => {
                const response = JSON.parse(xhr.responseText);
                const errorMessage = $('<div class="alert alert-danger"></div>').text(response.message);
                form.append(errorMessage);
            });
        });
    }).on('hide.bs.modal', () => {
        modalRequestSwitchuser.find('.alert-danger').remove();
        $('#modal-button-confirm-switchuser-request').unbind('click');
    });
});
