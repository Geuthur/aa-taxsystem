function setupModal(modalId, ajaxDataAttr, contentId, loaderId) {
    $(modalId).on('show.bs.modal', function (event) {
        const button = $(event.relatedTarget);
        let ajaxUrl = button.data(ajaxDataAttr);
        const modal = $(this);
        let hiddenUrl = modal.find('#modal-hidden-url').val();

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
    }).on('hidden.bs.modal', function () {
        // Clear the modal content when it is hidden
        $(this).find(contentId).html('');
    });
}
