function setupModal(modalId, ajaxDataAttr, contentId, loaderId) {
    $(modalId).on('show.bs.modal', function (event) {
        const button = $(event.relatedTarget);
        const ajaxUrl = button.data(ajaxDataAttr);
        const modal = $(this);

        // reactive loader
        modal.find(contentId).hide();
        modal.find(loaderId).show();

        modal.find(contentId).load(
            ajaxUrl,
            function(response, status, xhr) {
                modal.find(loaderId).hide();
                modal.find(contentId).show();

                if (xhr.status === 403) {
                    modal.find(contentId).html(response);
                }
                // Extract and set the modal title
                const title = modal.find(contentId).find('#modal-title').html();
                modal.find('.modal-title').html(title);
                modal.find(contentId).find('#modal-title').hide();
            }
        );
    });
}
