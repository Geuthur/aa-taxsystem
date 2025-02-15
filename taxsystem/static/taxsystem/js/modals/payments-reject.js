$(document).ready(() => {
    /* global tablePayments */
    /* global taxsystemsettings */
    const modalRequestDecline = $('#payments-reject');
    const modalRequestDeclineError = modalRequestDecline.find('#modal-error-field');
    const previousDeclineModal = $('#modalViewPaymentsContainer');

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

                $('#statistics_payments').text(stat.payments);
                $('#statistics_payments_pending').text(stat.payments_pending);
                $('#statistics_payments_auto').text(stat.payments_auto);
                $('#statistics_payments_manually').text(stat.payments_manually);
            },
            error: function(xhr, status, error) {
                console.error('Error fetching statistics data:', error);
            }
        });
    }

    // Decline Request Modal
    modalRequestDecline.on('show.bs.modal', (event) => {
        const button = $(event.relatedTarget);
        const url = button.data('action');

        // Extract the title from the button
        const modalTitle = button.data('title');
        const modalTitleDiv = modalRequestDecline.find('#modal-title');
        modalTitleDiv.html(modalTitle);

        // Extract the text from the button
        const modalText = button.data('text');
        const modalDiv = modalRequestDecline.find('#modal-request-text');
        modalDiv.html(modalText);

        $('#modal-button-confirm-reject-request').on('click', () => {
            const form = modalRequestDecline.find('form');
            const rejectInfoField = form.find('textarea[name="reject_reason"]');
            const rejectInfo = rejectInfoField.val();
            const csrfMiddlewareToken = form.find('input[name="csrfmiddlewaretoken"]').val();

            if (rejectInfo === '') {
                modalRequestDeclineError.removeClass('d-none');
                rejectInfoField.addClass('is-invalid');

                // Add shake class to the error field
                modalRequestDeclineError.addClass('ts-shake');

                // Remove the shake class after 3 seconds
                setTimeout(() => {
                    modalRequestDeclineError.removeClass('ts-shake');
                }, 2000);
            } else {
                const posting = $.post(
                    url,
                    {
                        reject_reason: rejectInfo,
                        csrfmiddlewaretoken: csrfMiddlewareToken
                    }
                );

                posting.done((data) => {
                    if (data.success === true) {
                        modalRequestDecline.modal('hide');
                        // Reload the AJAX request from the previous modal
                        const previousModalUrl = previousDeclineModal.find('#modal-hidden-url').val();
                        if (previousModalUrl) {
                            // Reload the parent modal with the same URL
                            $('#modalViewPaymentsContainer').modal('show');

                            // Reload the statistics
                            reloadStatistics();
                        } else {
                            // Reload with no Modal
                            const paymentsTable = $('#payments').DataTable();
                            paymentsTable.ajax.reload();
                        }
                    }
                }).fail((xhr, _, __) => {
                    const response = JSON.parse(xhr.responseText);
                    const errorMessage = $('<div class="alert alert-danger"></div>').text(response.message);
                    form.append(errorMessage);
                });
            }
        });
    }).on('hide.bs.modal', () => {
        modalRequestDecline.find('textarea[name="reject_reason"]').val('');
        modalRequestDecline.find('textarea[name="reject_reason"]').removeClass('is-invalid');
        modalRequestDecline.find('.alert-danger').remove();
        modalRequestDeclineError.addClass('d-none');
        $('#modal-button-confirm-reject-request').unbind('click');
    });
});
