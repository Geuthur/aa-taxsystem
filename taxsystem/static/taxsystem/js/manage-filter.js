$(document).ready(() => {
    /* global tableFilter */
    /* global taxsystemsettings */
    const modalRequestFilter = $('#filter-set-delete-filter');

    // Decline Request Modal
    modalRequestFilter.on('show.bs.modal', (event) => {
        const button = $(event.relatedTarget);
        const url = button.data('action');

        // Extract the title from the button
        const modalTitle = button.data('title');
        const modalTitleDiv = modalRequestFilter.find('#modal-title');
        modalTitleDiv.html(modalTitle);

        // Extract the text from the button
        const modalText = button.data('text');
        const modalDiv = modalRequestFilter.find('#modal-request-text');
        modalDiv.html(modalText);

        $('#modal-button-confirm-approve-request').on('click', () => {
            const form = modalRequestFilter.find('form');
            const rejectInfoField = form.find('textarea[name="delete_reason"]');
            const rejectInfo = rejectInfoField.val();
            const csrfMiddlewareToken = form.find('input[name="csrfmiddlewaretoken"]').val();

            const posting = $.post(
                url,
                {
                    delete_reason: rejectInfo,
                    csrfmiddlewaretoken: csrfMiddlewareToken
                }
            );

            posting.done((data) => {
                if (data.success === true) {
                    modalRequestFilter.modal('hide');
                    // Reload the parent modal
                    $('#modalViewFilterContainer').modal('show');
                }
            }).fail((xhr, _, __) => {
                const response = JSON.parse(xhr.responseText);
                const errorMessage = $('<div class="alert alert-danger"></div>').text(response.message);
                form.append(errorMessage);
            });
        });
    }).on('hide.bs.modal', () => {
        modalRequestFilter.find('textarea[name="delete_reason"]').val('');
        modalRequestFilter.find('.alert-danger').remove();
        $('#modal-button-confirm-approve-request').unbind('click');
        // Reload the parent modal
        $('#modalViewFilterContainer').modal('show');
    });
});

$(document).ready(() => {
    const filterTableVar = $('#filters');

    const tableFilter = filterTableVar.DataTable({
        'order': [[ 0, 'desc' ]],
        'columnDefs': [
            { 'orderable': false, 'targets': [2, 3] },
        ]
    });

    tableFilter.on('draw', function () {
        $('[data-tooltip-toggle="taxsystem-tooltip"]').tooltip({
            trigger: 'hover',
        });
    });

    // Tooltip
    $('[data-tooltip-toggle="taxsystem-tooltip"]').tooltip({
        trigger: 'hover',
    });
});
