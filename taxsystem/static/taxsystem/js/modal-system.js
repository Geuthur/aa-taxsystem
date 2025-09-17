let previousModal = null;

// Function to setup a modal with AJAX content loading
function setupModal(modalId, ajaxDataAttr, contentId, loaderId) {
    $(modalId).on('show.bs.modal', function (event) {
        const button = $(event.relatedTarget);
        let ajaxUrl = button.data(ajaxDataAttr);
        const modal = $(this);
        let hiddenUrl = modal.find('#modal-hidden-url').val();

        // Save the previous modal to reload it on close
        previousModal = $(button.closest('.modal'));

        // If ajaxUrl does not exist, use hiddenUrl
        if (!ajaxUrl) {
            ajaxUrl = hiddenUrl;
        }

        if (!ajaxUrl) {
            return;
        }

        // reactive loader
        modal.find(contentId).hide();
        modal.find(loaderId).show();

        modal.find(contentId).load(
            ajaxUrl,
            function(response, status, xhr) {
                modal.find(loaderId).hide();
                modal.find(contentId).show();

                if ([403, 404, 500].includes(xhr.status)) {
                    modal.find(contentId).html(response);
                    modal.find('.modal-title').html('Error');
                    return;
                }

                // Extract and set the modal title
                const title = modal.find(contentId).find('#modal-title').html();
                modal.find('.modal-title').html(title);
                modal.find('.modal-title').removeClass('d-none');
                modal.find(contentId).find('#modal-title').hide();

                // Set the hidden URL for conformation process
                modal.find('#modal-hidden-url').val(ajaxUrl);
            }
        );
    }).on('hide.bs.modal', () => {
        // Clear the modal content when it is hidden
        $(this).find(contentId).html('');
        // Reload the previous modal if it exists
        if (previousModal) {
            previousModal.modal('show');
            previousModal = null;
        }
    });
}
