/**
 * alert.js
 *
 * Create modal window,
 *
 * Features:
 *  show - show modal window
 *  close - call alertBox.options.cancel function or close modal window
 *  accept - call alertBox.options.bind function
 *    - close modal window if function return true
 *    - show error message if function return false
 *  setOptions {Object} - alert:parameters
 *    - bind {Function} - callback function when "accept" button is pressed
 *    - cancel {Function} - callback function when "cancel" button is pressed
 *    - accept_text {String} - inner text or HTML
 *    - accept_hide {Boolean} - hide "accept" button (default: false)
 *    - closeModal {Function} - close modal window callback function
 */

class Alert {
    constructor() {
        this.options = {};
    }

    show() {
        // close all modal windows
        closeModal();

        const modalBody = document.getElementById("modal_body");
        modalBody.innerHTML = this.options.text instanceof Node ? "" : this.options.text;
        if (this.options.text instanceof Node) {
            modalBody.appendChild(this.options.text);
        }

        // hide modal error block
        document.getElementById("modal_feedback").classList.add("visually-hidden");

        // change "accept" button text and visibility
        const acceptButton = document.getElementById("modal_save");
        acceptButton.innerHTML = this.options.accept_text || "Save changes";
        acceptButton.hidden = !!this.options.accept_hide;

        // show modal window
        showModal(this.options);

        // "Escape" key event
        const alertElement = document.getElementById("alert");
        alertElement.addEventListener("keyup", this.keyup.bind(this), false);

        // change focus to first input element
        const input = $("#modal_body :input:visible:enabled:first").focus();
        if (!input.length) {
            alertElement.focus();
        }

        return this;
    }

    cancel() {
        // close modal window if "close" button pressed
        if (typeof this.options.cancel === "function") {
            this.options.cancel();
        } else {
            this.closeModal();
        }
    }

    accept() {
        // "Save changes" button click event
        const result = typeof this.options.bind === "function" ? this.options.bind() : true;
        if (result) {
            this.closeModal();
        }
        return this;
    }

    keyup(e) {
        // "Escape" key event
        if (e.key === "Escape") {
            if (e.target.options && typeof e.target.options.closeModal === "function") {
                e.target.options.closeModal();
            } else {
                closeModal();
            }
        }
    }

    closeModal() {
        // close modal window
        if (typeof this.options.closeModal === "function") {
            this.options.closeModal();
        } else {
            closeModal();
        }
    }

    setOptions(options) {
        this.options = options;
        return this;
    }
}

/**
 * Show modal window global function.
 */
function showModal(options) {
    const modals = document.getElementsByClassName("modal");
    if (modals.length === 0) return;

    const backdrop = document.createElement("div");
    backdrop.className = "backdrop modal-backdrop show";
    document.body.appendChild(backdrop);

    Array.from(modals).forEach(modal => {
        modal.options = options;
        modal.classList.add("show", "d-block");
    });
}

/**
 * Close modal window global function.
 */
function closeModal() {
    const modals = document.getElementsByClassName("modal");
    Array.from(modals).forEach(modal => modal.classList.remove("show", "d-block"));

    const backdrops = document.getElementsByClassName("backdrop");
    Array.from(backdrops).forEach(backdrop => backdrop.remove());

    const acceptButton = document.getElementById("modal_save");
    acceptButton.disabled = false;
    acceptButton.hidden = false;
}

/**
 * Replacement default browser alert.
 */
window.alert = function (text) {
    const div = document.createElement("div");
    div.className = "text-break";
    div.innerHTML = text;

    return alertBox.setOptions({
        text: div,
        bind: undefined,
        accept_hide: true
    }).show();
};


const alertBox = new Alert();
