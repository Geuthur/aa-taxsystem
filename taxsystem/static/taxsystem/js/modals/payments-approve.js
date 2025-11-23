$(document).ready(() => {
    /* global paymentsTable */
    /* global taxsystemsettings */
    /* global reloadStatistics */
    /* global paymentsystemTable */

    const modalRequestApprove = $('#payments-approve');
    const previousApproveModal = $('#modalViewPaymentsContainer');

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
            const approveInfoField = form.find('textarea[name="accept_info"]');
            const approveInfo = approveInfoField.val();
            const csrfMiddlewareToken = form.find('input[name="csrfmiddlewaretoken"]').val();

            const posting = $.post(
                url,
                {
                    accept_info: approveInfo,
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
                        // Reload the payment system table
                        paymentsystemTable.DataTable().ajax.reload();
                        // Reload the statistics
                        reloadStatistics();
                    } else {
                        // Reload with no Modal
                        paymentsTable.DataTable().ajax.reload();
                    }
                }
            }).fail((xhr, _, __) => {
                const response = JSON.parse(xhr.responseText);
                const errorMessage = $('<div class="alert alert-danger"></div>').text(response.message);
                form.append(errorMessage);
            });
        });
    }).on('hide.bs.modal', () => {
        modalRequestApprove.find('textarea[name="accept_info"]').val('');
        $('#modal-button-confirm-approve-request').unbind('click');
        // Reload the AJAX request from the previous modal
        $('#modalViewPaymentsContainer').modal('show');
    });
});
