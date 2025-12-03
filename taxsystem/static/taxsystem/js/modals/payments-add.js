$(document).ready(() => {
    /* global taxsystemsettings */
    /* global reloadStatistics */
    /* global paymentsystemTable */
    /* global paymentsTable */

    const modalRequestAdd = $('#payments-add');
    const modalRequestDeclineError = modalRequestAdd.find('#modal-error-field');

    /**
     * Reset a modal to its initial state.
     * - resets the form
     * - clears validation state and error messages
     * - hides the error field
     * - unbinds confirm button handlers inside the modal
     */
    function resetModal(modal) {
        const form = modal.find('form');
        if (form.length) {
            form.trigger('reset');
        }

        modal.find('.is-invalid').removeClass('is-invalid');
        modal.find('.alert-danger').remove();

        const errorField = modal.find('#modal-error-field');
        if (errorField.length) {
            errorField.addClass('d-none');
            errorField.removeClass('ts-shake');
        }

        // Unbind any confirm buttons inside this modal (id prefix used to locate confirm buttons)
        modal.find('[id^="modal-button-confirm"]').off('click');
    }

    // Decline Request Modal
    modalRequestAdd.on('show.bs.modal', (event) => {
        const button = $(event.relatedTarget);
        const url = button.data('action');

        // Extract the title from the button
        const modalTitle = button.data('title');
        const modalTitleDiv = modalRequestAdd.find('#modal-title');
        modalTitleDiv.html(modalTitle);

        // Extract the text from the button
        const modalText = button.data('text');
        const modalDiv = modalRequestAdd.find('#modal-request-text');
        modalDiv.html(modalText);

        $('#modal-button-confirm-add-request').on('click', () => {
            const form = modalRequestAdd.find('form');
            const addInfoField = form.find('textarea[name="add_reason"]');
            const addAmountField = form.find('input[name="amount"]');
            const addInfo = addInfoField.val();
            const addAmount = addAmountField.val();
            const csrfMiddlewareToken = form.find('input[name="csrfmiddlewaretoken"]').val();

            if (addInfo === '') {
                modalRequestDeclineError.removeClass('d-none');
                addInfoField.addClass('is-invalid');

                // Add shake class to the error field
                modalRequestDeclineError.addClass('ts-shake');

                // Remove the shake class after 3 seconds
                setTimeout(() => {
                    modalRequestDeclineError.removeClass('ts-shake');
                }, 2000);
            } else if (addAmount === '' || isNaN(addAmount) || Number(addAmount) <= 0) {
                modalRequestDeclineError.removeClass('d-none');
                addAmountField.addClass('is-invalid');

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
                        add_reason: addInfo,
                        amount: addAmount,
                        csrfmiddlewaretoken: csrfMiddlewareToken
                    }
                );

                posting.done((data) => {
                    if (data.success === true) {
                        modalRequestAdd.modal('hide');
                        // Reload All Relevant Tables
                        paymentsTable.DataTable().ajax.reload();
                        paymentsystemTable.DataTable().ajax.reload();
                        reloadStatistics();
                    }
                }).fail((xhr, _, __) => {
                    const response = JSON.parse(xhr.responseText);
                    const errorMessage = $('<div class="alert alert-danger"></div>').text(response.message);
                    form.append(errorMessage);
                });
            }
        });
    }).on('hide.bs.modal', () => {
        // Use shared reset helper to clear form state and handlers
        resetModal(modalRequestAdd);
    });
});
