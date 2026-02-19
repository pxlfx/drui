/**
 * core.js
 */

let _core_;

(function () {
    class Core {
        constructor() {
            this.theme = this.getTheme();
            this.setTheme(this.theme);

            // change favicon
            const light_icon = document.querySelector("link#light_icon");
            const dark_icon = document.querySelector("link#dark_icon");
            if (this.getTheme(false) === "dark") {
                if (light_icon) light_icon.remove();
                document.head.append(dark_icon);
            } else {
                if (dark_icon) dark_icon.remove();
                document.head.append(light_icon);
            }
        }

        /**
         * Return active theme name.
         *
         * @param {boolean} cache - use cache
         * @return {string} active theme name
         */
        getTheme(cache = true) {
            let theme = localStorage.getItem("core::theme");
            if (!theme || !cache) {
                theme = window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
            }
            return theme;
        }

        /**
         * Set active theme.
         *
         * @param {string} theme - theme name
         */
        setTheme(theme) {
            this.theme = theme;
            document.documentElement.setAttribute("data-bs-theme", theme);
            localStorage.setItem("core::theme", theme);
        }

        /**
         * Toggle active theme.
         */
        toggleTheme() {
            const newTheme = this.theme === "dark" ? "light" : "dark";
            const is_dark = newTheme === "dark";
            this.setTheme(newTheme);

            const core_theme_box = document.getElementsByClassName("core_theme");
            [...core_theme_box].forEach((element) => {
                if (element.nodeName === "INPUT" && element.type === "checkbox") {
                    element.checked = is_dark;
                } else if (element.nodeType !== "SVG") {
                    element.classList.toggle("fa-sun");
                    element.classList.toggle("fa-moon");
                }
            });
        }
    }

    _core_ = new Core();
})();


window.onload = () => {
    // create theme icon
    const is_dark = _core_.theme === "dark";
    const theme_icon = is_dark ? "fa fa-moon" : "fa fa-sun";

    const core_theme_box = document.getElementsByClassName("core_theme");
    [...core_theme_box].forEach((element) => {
        if (element.nodeName === "INPUT" && element.type === "checkbox") {
            element.checked = is_dark;
        } else {
            const i = document.createElement("i");
            i.className = `${theme_icon} core_theme small`;
            element.appendChild(i);
        }
    });

    // activate tooltips
    tooltip();
};


/**
 * Check data for emptiness.
 *
 * @param {*} data
 * @return {boolean} true if data is empty, else false
 */
function isEmpty(data) {
    if (data === null || data === undefined) return true;
    if (Array.isArray(data) && !data.length) return true;
    if (typeof data === "object" && !Object.keys(data).length) return true;
    return typeof data === "string" && !data.length;
}


/**
 * Transformation bytes to KB, MB, GB, TB, PB.
 *
 * @param {number|string} bytes - bytes
 * @return {number|string} transformation size or NaN
 */
function sizeFormat(bytes) {
    let size = parseInt(bytes);
    if (isNaN(size)) {
        console.warn(`core.js: sizeFormat() error: character "${bytes}" cannot be converted to a number.`);
        return NaN;
    }

    const units = ["B", "KB", "MB", "GB", "TB", "PB"];
    let unit_index = 0;
    while (size >= 1000 && unit_index < units.length - 1) {
        size /= 1000;
        unit_index++;
    }
    return `${size.toFixed(2)} ${units[unit_index]}`;
}


/**
 * Formatting Date with template.
 *
 * %Y - year
 * %M - month
 * %D - day
 * %h - hour
 * %m - minute
 * %s - second
 *
 * @param {string} f - date template (example: %Y-%M-%D, %h:%m:%s)
 * @return {string} - formatting date
 */
Date.prototype.format = function (f) {
    const replacements = {
        "%Y": this.getFullYear().toString(),
        "%M": ("0" + (this.getMonth() + 1)).slice(-2),
        "%D": ("0" + this.getDate()).slice(-2),
        "%h": ("0" + this.getHours()).slice(-2),
        "%m": ("0" + this.getMinutes()).slice(-2),
        "%s": ("0" + this.getSeconds()).slice(-2)
    };

    for (const [key, value] of Object.entries(replacements)) {
        f = f.replace(new RegExp(key, "g"), value);
    }
    return f;
};


/**
 * Create <span> element with last modified time.
 *
 * @param {number|string} date - time (in seconds)
 * @returns {HTMLSpanElement}
 */
function lastModified(date) {
    let today = new Date();
    let last_modified = new Date(date);
    let delta = parseInt(((today - last_modified) / 86400000).toFixed());

    let span = document.createElement("span");
    span.title = last_modified.format("%Y-%M-%D, %h:%m:%s");
    span.className = "text-nowrap";
    span.setAttribute("data-bs-toggle", "tooltip");

    if (delta / 365 > 0) {
        span.textContent = (delta / 365).toFixed() + " years ago";
    }

    if (delta < 365) {
        span.textContent = (delta / 30).toFixed() + " months ago";
    }

    if (delta < 30) {
        span.textContent = delta + " days ago";
    }

    if (delta === 0) {
        span.textContent = "today";
    }

    return span;
}


/**
 * Create button.
 *
 * @param {Object} options - button parameters:
 *   - {string} id - button id
 *   - {string} text - button text
 *   - {string} icon - fa css-class (see FontAwesome)
 *   - {string} title - button title
 *   - {Object} tooltip - tooltip parameters (see Bootstrap/Components/Tooltips)
 *   - {string} className - button CSS classes (separator: both)
 *   - {function} callback - callback function
 *  @return {HTMLDivElement} button
 */
function createButton(options = {}) {
    const button = document.createElement("div");
    button.className = options.className ? `${options.className} badge` : "badge";

    if (options.id) button.id = options.id;

    if (options.text) {
        const span = document.createElement("span");
        span.textContent = options.text;
        button.appendChild(span);
    }

    if (options.icon) {
        const i = document.createElement("i");
        i.className = `fa ${options.icon} ${options.text ? "me-1 small" : ""}`;
        button.prepend(i);
    }

    if (options.title) {
        button.title = options.title;
        button.setAttribute("data-bs-toggle", "tooltip");
        button.setAttribute("data-bs-placement", options.tooltip?.placement || "top");
        button.setAttribute("data-bs-title", options.title);
    }

    if (options.callback && typeof options.callback === "function") {
        button.addEventListener("click", options.callback);
        button.classList.add("btn");
    } else {
        button.style.cursor = "default";
    }

    return button;
}


/**
 * Show modal window error block.
 *
 * @param {string|HTMLElement} text - inner text or HTML
 */
function modal_error(text) {
    let feedback = document.getElementById("modal_feedback");
    feedback.children[0].innerText = text;
    feedback.classList.remove("visually-hidden");
}


/**
 * Highlight text.
 *
 * @param {*} text - text to highlight
 * @param {HTMLElement} element - target DOM element
 */
function highlight(text, element) {
    const formatJson = (text) => {
        if (typeof text === "object") {
            return JSON.stringify(text, null, 4);
        }

        try {
            return JSON.stringify(JSON.parse(text), null, 4);
        } catch (error) {
            return text.replace(/"/g, "'");
        }
    };

    const converter = new showdown.Converter({
        tables: true,
        tasklists: true,
        simplifiedAutoLink: true,
    });
    const sanitizedJson = converter.makeHtml("```json\n" + formatJson(text) + "\n```");
    const tempDiv = document.createElement('div');
    tempDiv.innerHTML = sanitizedJson;
    element.appendChild(tempDiv);
    hljs.highlightElement(element.getElementsByTagName("code")[0]);
}


/**
 * Copy text to clipboard.
 *
 * @param {string} text - text
 * @param {HTMLElement} element - DOM element for a temporary block
 */
function copyToClipboard(text, element) {
    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text);
    } else {
        const text_area = document.createElement("textarea");
        text_area.value = text;
        text_area.style.position = "absolute";
        text_area.style.left = "0";
        element ? element.appendChild(text_area) : document.body.appendChild(text_area);
        text_area.tabIndex = 0;
        text_area.select();

        try {
            document.execCommand("copy");
        } catch (error) {
            console.error(error);
        } finally {
            text_area.remove();
        }
    }
}


/**
 * Create input element with clipboard button.
 *
 * @param {string} text - input element text
 * @param {Object} options - parameters:
 *   - {string} className - CSS classes of element
 * @return {HTMLDivElement} input element with clipboard button
 */
function clipboard(text, options = {}) {
    const icon = document.createElement("i");
    icon.className = `fa fa-clipboard align-middle ${options.className}`;

    const div = document.createElement("div");
    div.role = "button";
    div.className = "px-2 py-1";
    div.tabIndex = 1;
    div.appendChild(icon);

    div.addEventListener("click", () => {
        copyToClipboard(text, div);
        const icon = div.firstChild;
        icon.classList.remove("fa-clipboard");
        icon.classList.add("fa-clipboard-check");
        setTimeout(() => {
            const icon = div.firstChild;
            icon.classList.remove("fa-clipboard-check");
            icon.classList.add("fa-clipboard");
        }, 5000);
    });

    return div;
}


/**
 * Displays a Bootstrap Offcanvas modal with a copy-to-clipboard button.
 * The Offcanvas is only triggered on screens narrower than `max_width` (default: 993px).
 *
 * @param {string} text - text to display
 * @param {number} max_width - (optional) maximum window width (in px) to generate offcanvas
 */
function offcanvasClipboard(text, max_width = 993) {
    if (window.innerWidth > max_width) return;

    const active_menu = document.getElementById("offcanvasActionMenu");
    const offcanvas = new bootstrap.Offcanvas(active_menu);
    const offcanvas_header = active_menu.querySelectorAll(".offcanvas-header")[0];
    const offcanvas_body = active_menu.querySelectorAll(".offcanvas-body")[0];

    highlight(text, offcanvas_body);

    offcanvas_header.prepend(
        clipboard(text, { className: "text-muted" })
    );
    const handler = () => {
        offcanvas_header.firstChild.remove();
        active_menu.removeEventListener("hidden.bs.offcanvas", handler);
    };
    active_menu.addEventListener("hidden.bs.offcanvas", handler);

    offcanvas.show();
}


/**
 * Return mark of image.
 *
 * @param {string} image - name of image
 * @return {string|undefined} mark
 */
function imageMark(image) {
    for (const prefix of verified_prefix) {
        if (image.startsWith(prefix)) return "verified";
    }
    for (const prefix of official_prefix) {
        if (image.startsWith(prefix)) return "official";
    }
    return "";
}


/**
 * Transformation image mark to DOM element.
 *
 * @param {string} mark -image mark
 * @param {Object} options - parameters (see: createButton function)
 * @return {HTMLElement} DOM element of image mark
 */
function markToBadge(mark, options = {}) {
    const badges = {
        official: {
            text: "Official Image",
            icon: "fa-certificate",
            className: "text-success opacity-75",
            title: "Official Images are a curated set of Docker open source."
        },
        verified: {
            text: "Verified Publisher",
            icon: "fa-shield",
            className: "text-primary opacity-75",
            title: "High-quality images from publishers verified by administration."
        },
        "": {
            text: "",
            icon: "fa-sun",
            className: "text-secondary opacity-0",
            title: "High-quality images from publishers verified by administration."
        }
    };

    return mark in badges ? createButton({ ...badges[mark], ...options }) : document.createElement("div");
}


/**
 * initialize tooltips.
 */
function tooltip() {
    document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach((el) => new bootstrap.Tooltip(el));
}
