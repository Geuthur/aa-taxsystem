$(document).ready(() => {
    // * global tablePayments */
    const modalRequestDecline = $('#payments-decline');
    const modalRequestDeclineError = modalRequestDecline.find('#modal-error-field');
    const previousDeclineModal = $('#modalViewPaymentsContainer');

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

        $('#modal-button-confirm-decline-request').on('click', () => {
            const form = modalRequestDecline.find('form');
            const declineInfoField = form.find('textarea[name="decline_reason"]');
            const declineInfo = declineInfoField.val();
            const csrfMiddlewareToken = form.find('input[name="csrfmiddlewaretoken"]').val();

            if (declineInfo === '') {
                modalRequestDeclineError.removeClass('d-none');
                declineInfoField.addClass('is-invalid');

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
                        decline_reason: declineInfo,
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
        modalRequestDecline.find('textarea[name="decline_reason"]').val('');
        modalRequestDecline.find('textarea[name="decline_reason"]').removeClass('is-invalid');
        modalRequestDecline.find('.alert-danger').remove();
        modalRequestDeclineError.addClass('d-none');
        $('#modal-button-confirm-decline-request').unbind('click');
    });
});
