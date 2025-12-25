$(function () {
    const flat_metrics = flattenObject(metrics);

    Object.keys(flat_metrics).forEach((key) => {
        let value = flat_metrics[key];
        if (!value) {
            return;
        }

        switch (key) {
            case "stats.timestamp":
                value = new Date(value * 1000).format("%Y/%M/%D %h:%m");
                break;

            case "stats.status":
                const status_dict = {
                    "in progress": "badge text-bg-warning",
                    completed: "badge text-bg-success",
                    error: "badge text-bg-danger",
                };
                const span = document.createElement("span");
                span.className = status_dict[value];
                span.innerText = value;
                value = span;
                break;

            case "size":
                value = sizeFormat(value);
                break;

            case "newest":
            case "oldest":
                if (!value.length) {
                    value = "No images found";
                } else {
                    const dl = document.createElement("dl");
                    dl.className = "row";

                    const dt_header = document.createElement("dt");
                    dt_header.className = "col-8 fw-bold pb-1";
                    dt_header.innerText = "image";
                    dl.appendChild(dt_header);

                    const dd_header = document.createElement("dd");
                    dd_header.className = "col-2 fw-normal text-end fw-bold pb-1";
                    dd_header.innerText = "created";
                    dl.appendChild(dd_header);

                    value.forEach((item) => {
                        const [repo, tag] = item.image.split(":");

                        const dt = document.createElement("dt");
                        dt.className = "col-8 text-nowrap text-truncate pb-1 fw-normal";
                        dt.innerHTML = `<a href="/_/${repo}/tags/${tag}"">${item.image}</a>`;
                        dl.appendChild(dt);

                        const dd = document.createElement("dd");
                        dd.className = "col-2 fw-normal text-end pb-1";
                        dd.appendChild(lastModified(item.created));
                        dd.role = "button";
                        dl.appendChild(dd);
                    });
                    value = dl;
                }
                break;

            case "dublicates":
                if (!value.length) {
                    value = "No dublicates found";
                } else {
                    const div = document.createElement("div");
                    value.forEach((item) => {
                        const title = document.createElement("div");
                        title.className = "fw-bold text-muted mt-3";
                        title.innerText = `digest: ${item.digest}`;
                        div.appendChild(title);
                        div.appendChild(getList(item.images));
                    });
                    value = div;
                }
                break;

            default:
                value = JSON.stringify(value || "");
                break;
        }

        const dom = document.getElementById(key);
        if (dom) {
            if (value instanceof Element) {
                dom.appendChild(value);
            } else {
                dom.innerHTML = value;
            }
        }
    });
});


/**
 * Flattens a nested object into a single-level object.
 *
 * @param {Object} obj - the nested object to flatten
 * @param {string} parentKey - (internal) parent key path
 * @param {Object} result - (internal) accumulator object
 * @return {Object} single-level object
 */
function flattenObject(obj, parentKey = "", result = {}) {
    for (let key in obj) {
        if (obj.hasOwnProperty(key)) {
            const newKey = parentKey ? `${parentKey}.${key}` : key;
            const value = obj[key];

            if (typeof value === "object" && value !== null) {
                if (Array.isArray(value)) {
                    result[newKey] = value;
                } else {
                    flattenObject(value, newKey, result);
                }
            } else {
                result[newKey] = value;
            }
        }
    }
    return result;
}


/**
 * Generates a list of image tag links.
 *
 * @param {Array} images - list of images in the format "image:tag"
 * @returns {HTMLElement} - "<ol>" element with list items
 */
function getList(images) {
    const ol = document.createElement("ol");
    ol.className = "list-group list-group-numbered";
    images.forEach((image) => {
        const [repo, tag] = image.split(":");
        const li = document.createElement("li");
        li.innerHTML = `<a href="/_/${repo}/tags/${tag}">${image}</a>`;
        li.className = "list-group-item text-truncate w-100 border-0 py-1";
        ol.appendChild(li);
    });

    return ol;
}
