$(document).ready(() => {
    /* global tablePayments */
    /* global taxsystemsettings */
    const modalRequestApprove = $('#payments-approve');
    const previousApproveModal = $('#modalViewPaymentsContainer');

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

    // Approve Request Modal
    modalRequestApprove.on('show.bs.modal', (event) => {
        const button = $(event.relatedTarget);
        const url = button.data('action');

        // Extract the title from the button
        const modalTitle = button.data('title');
        const modalTitleDiv = modalRequestApprove.find('#modal-title');
        modalTitleDiv.html(modalTitle);

        // Extract the text from the button
        const modalText = button.data('text');
        const modalDiv = modalRequestApprove.find('#modal-request-text');
        modalDiv.html(modalText);

        $('#modal-button-confirm-approve-request').on('click', () => {
            const form = modalRequestApprove.find('form');
            const csrfMiddlewareToken = form.find('input[name="csrfmiddlewaretoken"]').val();

            const posting = $.post(
                url,
                {
                    csrfmiddlewaretoken: csrfMiddlewareToken
                }
            );

            posting.done((data) => {
                if (data.success === true) {
                    modalRequestApprove.modal('hide');
                    // Reload the AJAX request from the previous modal
                    const previousModalUrl = previousApproveModal.find('#modal-hidden-url').val();
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
        });
    }).on('hide.bs.modal', () => {
        modalRequestApprove.find('.alert-danger').remove();
        $('#modal-button-confirm-approve-request').unbind('click');
    });
});
