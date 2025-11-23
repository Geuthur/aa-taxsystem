$(document).ready(() => {
    /* global tablePayments */
    /* global taxsystemsettings */
    /* global reloadStatistics */
    /* global paymentsTable */

    const modalRequestUndo = $('#payments-undo');
    const modalRequestUndoError = modalRequestUndo.find('#modal-error-field');
    const previousUndoModal = $('#modalViewPaymentsContainer');

    // Undo Request Modal
    modalRequestUndo.on('show.bs.modal', (event) => {
        const button = $(event.relatedTarget);
        const url = button.data('action');

        // Extract the title from the button
        const modalTitle = button.data('title');
        const modalTitleDiv = modalRequestUndo.find('#modal-title');
        modalTitleDiv.html(modalTitle);

        // Extract the text from the button
        const modalText = button.data('text');
        const modalDiv = modalRequestUndo.find('#modal-request-text');
        modalDiv.html(modalText);

        $('#modal-button-confirm-undo-request').on('click', () => {
            const form = modalRequestUndo.find('form');
            const undoInfoField = form.find('textarea[name="undo_reason"]');
            const undoInfo = undoInfoField.val();
            const csrfMiddlewareToken = form.find('input[name="csrfmiddlewaretoken"]').val();

            if (undoInfo === '') {
                modalRequestUndoError.removeClass('d-none');
                undoInfoField.addClass('is-invalid');

                // Add shake class to the error field
                modalRequestUndoError.addClass('ts-shake');

                // Remove the shake class after 3 seconds
                setTimeout(() => {
                    modalRequestUndoError.removeClass('ts-shake');
                }, 2000);
            } else {
                const posting = $.post(
                    url,
                    {
                        undo_reason: undoInfo,
                        csrfmiddlewaretoken: csrfMiddlewareToken
                    }
                );

                posting.done((data) => {
                    if (data.success === true) {
                        modalRequestUndo.modal('hide');
                        // Reload the AJAX request from the previous modal
                        const previousModalUrl = previousUndoModal.find('#modal-hidden-url').val();
                        if (previousModalUrl) {
                            // Reload the parent modal with the same URL
                            $('#modalViewPaymentsContainer').modal('show');

                            // Reload the statistics
                            reloadStatistics();
                        } else {
                            // Reload with no Modal
                            paymentsTable.DataTable().ajax.reload();
                        }
                    } else {
                        console.log(data.message);
                        // Show the error message
                        const errorMessage = data.message;
                        $(errorMessage).insertAfter(undoInfoField);
                    }
                }).fail((xhr, _, __) => {
                    const response = JSON.parse(xhr.responseText);
                    const errorMessage = $('<div class="alert alert-danger"></div>').text(response.message);
                    form.append(errorMessage);
                });
            }
        });
    }).on('hide.bs.modal', () => {
        modalRequestUndo.find('textarea[name="undo_reason"]').val('');
        modalRequestUndo.find('textarea[name="undo_reason"]').removeClass('is-invalid');
        modalRequestUndo.find('.alert-danger').remove();
        modalRequestUndoError.addClass('d-none');
        $('#modal-button-confirm-undo-request').unbind('click');
        // Reload the AJAX request from the previous modal
        $('#modalViewPaymentsContainer').modal('show');
    });
});
