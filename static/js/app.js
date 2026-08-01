(() => {
    "use strict";

    const modalElement = document.getElementById("confirmationModal");
    const modalTitle = document.getElementById("confirmationModalTitle");
    const modalMessage = document.getElementById("confirmationModalMessage");
    const modalAccept = document.getElementById("confirmationModalAccept");
    let pendingForm = null;
    let pendingSubmitter = null;

    const clearPendingConfirmation = () => {
        pendingForm = null;
        pendingSubmitter = null;
    };

    const submitConfirmedForm = (form, submitter) => {
        form.dataset.confirmed = "true";
        if (submitter) {
            form.requestSubmit(submitter);
        } else {
            form.requestSubmit();
        }
    };

    document.querySelectorAll("form[data-confirm-message]").forEach((form) => {
        form.addEventListener("submit", (event) => {
            if (form.dataset.confirmed === "true") {
                delete form.dataset.confirmed;
                return;
            }

            const message = form.dataset.confirmMessage;
            if (!message) {
                return;
            }

            event.preventDefault();
            pendingForm = form;
            pendingSubmitter = event.submitter || null;

            if (!modalElement || !window.bootstrap) {
                const accepted = window.confirm(message);
                const formToSubmit = pendingForm;
                const submitter = pendingSubmitter;
                clearPendingConfirmation();
                if (accepted && formToSubmit) {
                    submitConfirmedForm(formToSubmit, submitter);
                }
                return;
            }

            if (modalTitle) {
                modalTitle.textContent =
                    form.dataset.confirmTitle || "Confirmar acción";
            }
            if (modalMessage) {
                modalMessage.textContent = message;
            }
            window.bootstrap.Modal.getOrCreateInstance(modalElement).show();
        });
    });

    modalAccept?.addEventListener("click", () => {
        const formToSubmit = pendingForm;
        const submitter = pendingSubmitter;
        clearPendingConfirmation();
        if (!formToSubmit) {
            return;
        }
        window.bootstrap?.Modal.getOrCreateInstance(modalElement)?.hide();
        submitConfirmedForm(formToSubmit, submitter);
    });

    modalElement?.addEventListener("hidden.bs.modal", clearPendingConfirmation);

    const invalidField = document.querySelector(
        "input[aria-invalid='true'], select[aria-invalid='true'], " +
        "textarea[aria-invalid='true'], input.is-invalid, " +
        "select.is-invalid, textarea.is-invalid"
    );
    if (invalidField instanceof HTMLElement) {
        invalidField.focus();
        return;
    }

    const feedback = document.querySelector(".invalid-feedback");
    const relatedField = feedback?.parentElement?.querySelector(
        "input, select, textarea"
    );
    if (relatedField instanceof HTMLElement) {
        relatedField.focus();
    }
})();
