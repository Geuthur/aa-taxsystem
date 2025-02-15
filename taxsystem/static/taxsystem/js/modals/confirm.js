/* global bootstrap */


// Modal
var confirmModal = document.getElementById('modalConfirmContainer');
var confirmTextSpan = document.getElementById('confirmText');
var confirmButton = document.getElementById('confirmButton');
var confirmTitleSpan = document.getElementById('confirmTitle');

// Reason Div
var confirmReasonDiv = document.getElementById('confirmationReason');
var confirmReasonLabel = document.getElementById('reasonLabel');
var confirmReasonText = document.getElementById('reasonText');
var reasonRequiredHint = document.getElementById('reasonRequirment');


confirmModal.addEventListener('show.bs.modal', function (event) {
    var button = event.relatedTarget;
    var formId = button.getAttribute('data-form-id');
    var reasonId = button.getAttribute('data-reason-id');
    var confirmText = button.getAttribute('data-confirm-text');
    var labelText = button.getAttribute('data-label');
    var title = button.getAttribute('data-title');
    var isRequired = button.getAttribute('data-required') === 'True';

    if (isRequired) {
        confirmReasonDiv.classList.remove('d-none');
    }

    confirmTextSpan.innerHTML = confirmText;
    confirmTitleSpan.innerHTML = title;
    confirmReasonLabel.innerHTML = labelText;

    confirmButton.onclick = function () {
        if (isRequired && confirmReasonText.value === '') {
            confirmReasonText.classList.add('is-invalid');
            reasonRequiredHint.classList.remove('d-none');
            return;
        }
        document.getElementById(reasonId).value = confirmReasonText.value;
        document.getElementById(formId).submit();
        var modal = bootstrap.Modal.getInstance(confirmModal);
        modal.hide();
    };
});

confirmModal.addEventListener('hidden.bs.modal', function () {
    confirmReasonText.value = '';
    confirmReasonText.classList.remove('is-invalid');
    reasonRequiredHint.classList.add('d-none');
    confirmReasonDiv.classList.add('d-none');
});
