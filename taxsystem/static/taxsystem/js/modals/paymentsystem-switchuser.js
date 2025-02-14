$(document).ready(() => {
    // * global tablePayments */
    const modalRequestSwitchuser = $('#paymentsystem-switchuser');

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
