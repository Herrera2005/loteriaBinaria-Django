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

(() => {
    "use strict";

    const navigation = document.getElementById("mainNavigation");
    const navigationToggle = document.querySelector(
        '[data-bs-target="#mainNavigation"]'
    );
    const mobileNavigationQuery = window.matchMedia("(max-width: 1199.98px)");

    if (!navigation || !window.bootstrap) {
        return;
    }

    const closeMobileNavigation = () => {
        if (!mobileNavigationQuery.matches) {
            return;
        }

        window.bootstrap.Offcanvas
            .getOrCreateInstance(navigation)
            .hide();
    };

    navigation.querySelectorAll(
        ".app-sidebar-nav a.nav-link, .app-sidebar-session a"
    ).forEach((link) => {
        link.addEventListener("click", closeMobileNavigation);
    });

    navigation.addEventListener("hidden.bs.offcanvas", () => {
        if (navigationToggle instanceof HTMLElement) {
            navigationToggle.focus();
        }
    });
})();

// P-35B-R3: ayuda visual para selección por posiciones.
// El servidor sigue siendo la única autoridad de validación y disponibilidad.
document.addEventListener("DOMContentLoaded", () => {
    const selection = document.querySelector("[data-ticket-selection]");
    if (!selection) return;

    const selects = Array.from(selection.querySelectorAll("select[data-ticket-position]"));

    const refreshDisabledOptions = () => {
        const selected = new Set(selects.map((field) => field.value).filter(Boolean));
        selects.forEach((field) => {
            Array.from(field.options).forEach((option) => {
                option.disabled = Boolean(
                    option.value && option.value !== field.value && selected.has(option.value)
                );
            });
        });
    };

    selects.forEach((field) => field.addEventListener("change", refreshDisabledOptions));
    refreshDisabledOptions();

    document.querySelectorAll("[data-availability-suggestion]").forEach((button) => {
        button.addEventListener("click", () => {
            const tokens = button.dataset.availabilitySuggestion.split("|");
            selects.forEach((field, index) => {
                field.value = tokens[index] || "";
            });
            refreshDisabledOptions();
            selects[0]?.focus();
        });
    });
});

// P-35C: prevención visual de símbolos repetidos al publicar el resultado.
// La validación definitiva permanece en DrawResultPublishForm y el servicio.
document.addEventListener("DOMContentLoaded", () => {
    const selection = document.querySelector("[data-result-selection]");
    if (!selection) return;

    const selects = Array.from(
        selection.querySelectorAll("select[data-result-position]")
    );

    const refreshDisabledOptions = () => {
        const selected = new Set(
            selects.map((field) => field.value).filter(Boolean)
        );
        selects.forEach((field) => {
            Array.from(field.options).forEach((option) => {
                option.disabled = Boolean(
                    option.value
                    && option.value !== field.value
                    && selected.has(option.value)
                );
            });
        });
    };

    selects.forEach((field) => {
        field.addEventListener("change", refreshDisabledOptions);
    });
    refreshDisabledOptions();
});

// P-36C-R1: creación unificada de eventos y series.
// Solo controla visibilidad; Django valida y guarda todos los datos.
document.addEventListener("DOMContentLoaded", () => {
    const buttons = Array.from(document.querySelectorAll("[data-creation-mode-button]"));
    const panels = Array.from(document.querySelectorAll("[data-creation-panel]"));
    if (buttons.length && panels.length) {
        const activate = (mode) => {
            buttons.forEach((button) => {
                const selected = button.dataset.creationModeButton === mode;
                button.classList.toggle("btn-primary", selected);
                button.classList.toggle("btn-outline-primary", !selected);
                button.setAttribute("aria-pressed", selected ? "true" : "false");
            });
            panels.forEach((panel) => {
                panel.hidden = panel.dataset.creationPanel !== mode;
            });
        };
        buttons.forEach((button) => {
            button.addEventListener("click", () => activate(button.dataset.creationModeButton));
        });
    }

    document.querySelectorAll("[data-series-form]").forEach((form) => {
        const modeInputs = Array.from(form.querySelectorAll("input[name$='occurrence_mode']"));
        const limitField = form.querySelector("[data-occurrence-limit-field]");
        if (!modeInputs.length || !limitField) return;

        const refreshLimit = () => {
            const selected = modeInputs.find((input) => input.checked)?.value;
            limitField.hidden = selected !== "LIMITED";
            const input = limitField.querySelector("input");
            if (input) input.disabled = selected !== "LIMITED";
        };
        modeInputs.forEach((input) => input.addEventListener("change", refreshLimit));
        refreshLimit();
    });
});
