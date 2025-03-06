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
            const light_icon = document.querySelector('link#light_icon');
            const dark_icon = document.querySelector('link#dark_icon');
            if (this.getTheme(false) === "dark") {
                light_icon.remove();
                document.head.append(dark_icon);
            } else {
                document.head.append(light_icon);
                dark_icon.remove();
            }
        }

        /**
         * Return active theme name.
         *
         * @param {boolean} cache: use cache
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
            this.setTheme(newTheme);

            const coreThemeIcon = document.getElementById("core_theme_icon");
            if (coreThemeIcon) {
                coreThemeIcon.classList.toggle("fa-sun");
                coreThemeIcon.classList.toggle("fa-moon");
            }
        }
    }

    _core_ = new Core();
}());


window.onload = () => {
    // create theme icon
    let theme_icon = _core_.theme === "dark" ? "fa fa-moon" : "fa fa-sun";
    let i = document.createElement("i");
    i.id = "core_theme_icon";
    i.className = `${theme_icon} small`;
    const core_theme_box = document.getElementById("core_theme");
    if (core_theme_box) core_theme_box.appendChild(i);

    // activate tooltips
    tooltip();
};

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

    const units = ['B', 'KB', 'MB', 'GB', 'TB', 'PB'];
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
        '%Y': this.getFullYear().toString(),
        '%M': ("0" + (this.getMonth() + 1)).slice(-2),
        '%D': ("0" + this.getDate()).slice(-2),
        '%h': ("0" + this.getHours()).slice(-2),
        '%m': ("0" + this.getMinutes()).slice(-2),
        '%s': ("0" + this.getSeconds()).slice(-2)
    };

    for (const [key, value] of Object.entries(replacements)) {
        f = f.replace(new RegExp(key, 'g'), value);
    }
    return f;
};


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
        i.className = `fa ${options.icon} ${options.text ? 'me-1 small' : ''}`;
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
 * @param {string|HTMLElement} text - inner text ot HTML
 */
function modal_error(text) {
    let feedback = document.getElementById("modal_feedback");
    feedback.children[0].innerHTML = text;
    feedback.classList.remove("visually-hidden");
}


/**
 * Create input element with clipboard button.
 *
 * @param {string} text - input element text
 * @param {Object} options - parameters:
 *   - {string} input_class_name - CSS classes of input element
 *   - {string} icon_class_name - CSS classes of clipboard button
 * @return {HTMLDivElement} input element with clipboard button
 */
function clipboard(text, options = {}) {
    const div = document.createElement("div");
    div.className = "input-group input-group-sm flex-nowrap form-control p-0";

    if (options.title) {
        div.setAttribute("data-bs-toggle", "tooltip");
        div.setAttribute("data-bs-title", options.title);
    }

    const input = document.createElement("input");
    input.type = "text";
    input.style.maxWidth = "200px";
    input.style.textOverflow = "ellipsis";
    input.className = `clipboard form-control text-start m-1 border-0 ${options.input_class_name || ''}`;
    input.value = text;

    const div_append = document.createElement("div");
    div_append.className = "input-group-append";

    const span = document.createElement("div");
    span.className = `input-group-text btn ${options.icon_class_name || ''}`;

    const i = document.createElement("i");
    i.className = "fa fa-clipboard";

    span.appendChild(i);
    div_append.appendChild(span);
    div.appendChild(input);
    div.appendChild(div_append);

    div_append.addEventListener("click", () => {
        if (navigator.clipboard && window.isSecureContext) {
            navigator.clipboard.writeText(input.value);
        } else {
            const text_area = document.createElement("textarea");
            text_area.value = input.value;
            text_area.style.position = "absolute";
            text_area.style.left = "-999999px";
            document.body.prepend(text_area);
            text_area.select();
            try {
                document.execCommand('copy');
            } catch (error) {
                console.error(error);
            } finally {
                text_area.remove();
            }
        }
    });

    return div;
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
            className: "text-success ps-0",
            title: "Official Images are a curated set of Docker open source."
        },
        verified: {
            text: "Verified Publisher",
            icon: "fa-shield",
            className: "text-primary ps-0",
            title: "High-quality images from publishers verified by administration."
        }
    };

    return mark in badges ? createButton({ ...badges[mark], ...options }) : document.createElement("div");
}


/**
 * initialize tooltips.
 */
function tooltip() {
    document.querySelectorAll('[data-bs-toggle="tooltip"]').forEach(el => new bootstrap.Tooltip(el));
}
