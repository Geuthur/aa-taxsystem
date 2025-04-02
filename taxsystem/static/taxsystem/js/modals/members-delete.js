$(document).ready(() => {
    /* global tablePayments */
    /* global taxsystemsettings */
    const modalRequestApprove = $('#members-delete-member');

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
            const deleteInfoField = form.find('textarea[name="delete_reason"]');
            const deleteInfo = deleteInfoField.val();
            const csrfMiddlewareToken = form.find('input[name="csrfmiddlewaretoken"]').val();

            const posting = $.post(
                url,
                {
                    delete_reason: deleteInfo,
                    csrfmiddlewaretoken: csrfMiddlewareToken
                }
            );

            posting.done((data) => {
                if (data.success === true) {
                    modalRequestApprove.modal('hide');

                    // Reload with no Modal
                    const paymentsTable = $('#members').DataTable();
                    paymentsTable.ajax.reload();
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
