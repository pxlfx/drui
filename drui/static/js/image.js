$(function () {
    // create element: `docker pull <image>:<tag>`
    const pull_text = `docker pull ${endpoint}/${image}:${tag}`;
    document.getElementById("pull").appendChild(
        clipboard(pull_text, {
            input_class_name: "mw-100",
            icon_class_name: "rounded-end",
            title: pull_text
        })
    );

    // set image mark
    const mark = imageMark(image);
    document.getElementById("mark").appendChild(markToBadge(mark, { text: "" }));

    // set summary image information
    setSummary();

    // set multiarch list
    setMultiarch();

    // set image history
    setHistory();

    // set image tags
    setTags();

    // set image inspect
    setInspect();

    // activate tooltips
    tooltip();
});


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
 * Return image size.
 * 
 * @param {Object} manifest - image manifest
 * @return {number} size of image (bytes)
 */
function getImageSize(manifest) {
    return manifest.layers.reduce((total, layer) => total + layer.size, 0);
}


/**
 * Set summary image tag information.
 */
function setSummary() {
    const summary_index = {
        "size": {
            icon: "fa fa-ruler",
            data: manifest,
            format: (x) => sizeFormat(getImageSize(x))
        },
        "os": {
            icon: "fa fa-chalkboard-user",
            data: manifest["os"]
        },
        "architecture": {
            icon: "fa fa-microchip",
            data: manifest["architecture"]
        },
        "created": {
            icon: "fa fa-clock",
            data: manifest["created"],
            format: (x) => new Date(x).format("%Y/%M/%D")
        },
        "id": {
            icon: "fa fa-square-binary",
            data: manifest["id"]
        },
        "digest": {
            icon: "fa fa-square-binary",
            data: manifest["digest"]
        },
        "cmd": {
            icon: "fa fa-hashtag",
            data: manifest["config"]["Cmd"],
            format: (x) => x.join(" ")
        },
        "labels": {
            icon: "fa fa-bookmark",
            data: manifest["config"]["Labels"],
            format: (x) => JSON.stringify(x, null, 4)
        },
        "volumes": {
            icon: "fa fa-server",
            data: manifest["config"]["Volumes"],
            format: (x) => JSON.stringify(x)
        },
        "entrypoint": {
            icon: "fa fa-location-dot",
            data: manifest["config"]["Entrypoint"],
            format: (x) => x.join("<br>")
        },
        "env": {
            icon: "fa fa-align-right",
            data: manifest["config"]["Env"],
            format: (x) => x.join("<br>")
        },
        "ports": {
            icon: "fa fa-wifi",
            data: manifest["config"]["ExposedPorts"],
            format: (x) => Object.keys(x).join("<br>")
        },
        "work dir": {
            icon: "fa fa-house",
            data: manifest["config"]["WorkingDir"]
        },
        "docker": {
            icon: "fa fa-docker",
            data: manifest["docker_version"]
        }
    }

    const dl = document.createElement("dl");
    dl.className = "row text-monospace";
    document.getElementById("summary-pane").appendChild(dl);

    Object.entries(summary_index).forEach(([key, { icon, data, format }]) => {
        if (isEmpty(data)) return;

        const i = document.createElement("i");
        i.className = `${icon} me-2 small`;

        const dt = document.createElement("dt");
        dt.className = "col-6 col-lg-2 text-nowrap pt-1 pb-1";
        dt.textContent = `${key}:`;
        dt.prepend(i);
        dl.appendChild(dt);

        const dd = document.createElement("dt");
        dd.className = "col-6 col-lg-10 pt-2 pb-2 fw-normal text-truncate text-end text-md-start";
        dd.innerHTML = format ? format(data) : data;
        dd.role = "button";
        dd.onclick = () => alert(dd.innerHTML);
        dl.appendChild(dd);
    });
}


/**
 * Set image history.
 */
function setHistory() {
    if (!manifest.history) return;

    const ol = document.createElement("ol");
    ol.className = "list-group list-group-numbered";
    manifest.history.forEach(value => {
        const li = document.createElement("li");
        li.textContent = value.created_by;
        li.className = "list-group-item list-group-item-action text-monospace text-truncate small w-100 border-0";
        li.role = "button";
        li.onclick = () => alert(li.innerText);
        ol.appendChild(li);
    });

    document.getElementById("history-pane").appendChild(ol);
}


/**
 * Set image tags.
 */
function setTags() {
    const ul = document.createElement("ol");
    ul.className = "list-group text-decoration-underline link-offset-3";
    tags.reverse().forEach(value => {
        const li = document.createElement("li");
        li.textContent = value;
        li.className = "list-group-item list-group-item-action text-monospace small text-truncate border-0";
        li.role = "button";
        li.onclick = () => window.location = `/_/${image}/tags/${value}`;
        ul.appendChild(li);
    });

    document.getElementById("tags-pane").appendChild(ul);
}


/**
 * Set multiarch.
 */
function setMultiarch() {
    const manifest_list = manifest.manifests || [{
        digest: manifest.digest,
        platform: {
            os: manifest.os,
            architecture: manifest.architecture
        }
    }];

    const ul = document.createElement("ol");
    ul.className = "list-group text-decoration-underline link-offset-3";
    manifest_list.forEach(x => {
        const li = document.createElement("li");
        li.textContent = `${x.platform.os}/${x.platform.architecture}`;
        li.className = "list-group-item list-group-item-action text-monospace small text-truncate border-0";
        li.role = "button";
        li.onclick = () => window.location = `/_/${image}/tags/${tag}?digest=${x.digest}`;
        ul.appendChild(li);
    });

    document.getElementById("multiarch-pane").appendChild(ul);
}


/**
 * Set image manifest.
 */
function setInspect() {
    const converter = new showdown.Converter({
        tables: true,
        tasklists: true,
        simplifiedAutoLink: true
    });

    const inspect_pane = document.getElementById("inspect-pane");
    inspect_pane.innerHTML = converter.makeHtml("```json\n" + JSON.stringify(manifest, null, 4) + "\n```");
    hljs.highlightAll();
}


/**
 * Show delete image box.
 *
 * @param {string} image - image name
 */
function deleteImage(image) {
    if (!image) {
        return false;
    }

    alertBox.setOptions({
        text: `<div>Select some image <b>${image}</b> tags:` +
            "<div class='mt-2' id='deleted_tags'></div>",
        accept_text: "Delete image tags" +
            "<i class='fa fa-gear fa-spin small align-middle ms-1 visually-hidden' id='gear'></i>",
        closeModal: () => {
            let table = document.getTableById("deleted_tags");
            table.selected = [];
            table._save_state();
            this.closeModal();
        },
        bind: function () {
            let deleted_tags = document.getTableById("deleted_tags").selected;
            let delete_errors = [];
            let delete_queue_count = deleted_tags.length;

            if (!deleted_tags.length) {
                modal_error("Please select some tags.");
                return false;
            }

            // animate delete process
            window.onbeforeunload = () => "";
            document.getElementById("modal_save").disabled = true;
            document.getElementById("modal_cancel").classList.add("visually-hidden");
            document.getElementById("gear").classList.remove("visually-hidden");

            new RequestQueue(
                deleted_tags,
                (tag) => {
                    return {
                        url: `/_/${image}/tags/${tag}`,
                        data: "format=json",
                        type: "DELETE",
                        async: true,
                        complete: (XHR) => {
                            delete_queue_count--;

                            if (XHR.status !== 200) {
                                delete_errors.push(`<b>${tag}</b>: ${XHR.responseText}`);
                            }

                            if (delete_queue_count === 0) {
                                window.onbeforeunload = undefined;
                                document.getElementById("modal_save").disabled = false;
                                document.getElementById("modal_cancel").classList.remove("visually-hidden");
                                document.getElementById("gear").classList.add("visually-hidden");

                                if (delete_errors.length) {
                                    modal_error(delete_errors.join("<br>"));
                                } else {
                                    alert("Delete finished.");
                                }
                            }
                        }
                    };
                },
                5
            ).run();

            return false;
        }
    }).show();

    new Table({
        element: document.getElementById("deleted_tags"),
        headers: [
            { name: "tag" },
        ],
        data: tags.map((x) => [x, x]),
        className: "table table-sm table-hover table-borderless",
        theadClassName: "table-sm",
        height: 200,
        index_by: 0,
        limit: 50,
        filter: true
    }).view();
}


/**
 * Show JSON in modal window.
 *
 * @param {Object} json - data in JSON
 */
function viewJSON(json) {
    alert("<div id='info'></div>");

    let data = [];
    Object.keys(json).forEach(function (key) {
        let val;
        if (typeof (json[key]) === "object") {
            val = JSON.stringify(json[key]);
        } else {
            val = json[key];
        }
        data.push([key, val]);
    });

    new Table({
        element: document.getElementById("info"),
        headers: [
            { name: "key" },
            {
                name: "value",
                format: (x) => clipboard(x, { input_class_name: "mw-100 bg-inherit" })
            }
        ],
        data: data,
        className: "table table-sm table-hover table-borderless",
        theadClassName: "table-sm",
        height: 700
    }).view();
}


/**
 * Parallel execution of ajax requests for a group of objects.
 *
 * @param {Array} queue - list of object names
 * @param {Object|Function} options - ajax-request parameters
 * @param {number} threads - number of simultaneously executing threads
 */
class RequestQueue {
    constructor(queue, options = {}, threads = 3) {
        this.workers = 0;

        // checking the passed parameters
        if (!Array.isArray(queue)) {
            throw new TypeError("Type of parameter 'queue' is not array");
        }
        this.queue = queue.slice();

        if (!["function", "object"].includes(typeof options)) {
            throw new TypeError("Type of parameter 'callback' is not function or object");
        }
        this.options = options;

        if (!threads) {
            throw new TypeError("Parameter 'threads' must be > 0");
        }
        this.threads = threads;
    }

    run() {
        let that = this;

        function next() {
            if (that.workers < that.threads && that.queue.length) {
                that.run()
            }
        }

        that.workers++;
        let unit = this.queue.shift();

        return new Promise(() => {
            let options = (typeof that.options === "function") ? that.options(unit) : that.options;
            let complete = options.complete;
            options.complete = (XDR, status) => {
                complete(XDR, status);
                that.workers--;
                next();
            };

            $.ajax(options);
            next();
        });
    }
}
