$(document).ready(() => {
    /* global tablePayments */
    /* global taxsystemsettings */
    /* global reloadStatistics */

    const modalRequestDecline = $('#payments-delete');
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

        $('#modal-button-confirm-delete-request').on('click', () => {
            const form = modalRequestDecline.find('form');
            const deleteInfoField = form.find('textarea[name="delete_reason"]');
            const deleteInfo = deleteInfoField.val();
            const csrfMiddlewareToken = form.find('input[name="csrfmiddlewaretoken"]').val();

            if (deleteInfo === '') {
                modalRequestDeclineError.removeClass('d-none');
                deleteInfoField.addClass('is-invalid');

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
                        delete_reason: deleteInfo,
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

                            // Reload the payment system table
                            const paymentsystemTable = $('#payment-system').DataTable();
                            paymentsystemTable.ajax.reload();

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
        // Reset the form to its initial state
        const form = modalRequestDecline.find('form');
        // trigger native reset (works for inputs, textareas, selects)
        form.trigger('reset');

        // Clear validation state and any appended error messages
        modalRequestDecline.find('.is-invalid').removeClass('is-invalid');
        modalRequestDecline.find('.alert-danger').remove();
        modalRequestDeclineError.addClass('d-none');
        $('#modal-button-confirm-delete-request').off('click');
        // Reload the AJAX request from the previous modal
        $('#modalViewPaymentsContainer').modal('show');
    });
});
