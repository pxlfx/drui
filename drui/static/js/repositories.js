// image.js: getting and displaying a list of Docker images.

$(function () {
    const filter_dom = document.getElementById("filter");
    if (filter_dom) {
        filter_dom.onkeyup = () => {
            const filtered_data = filterRepositories();
            viewRepositories(filtered_data);
        };
        filter_dom.dispatchEvent(new Event("keyup"));
    }

    viewBroadcast();
});


/**
 * Filters the repository list based on the input filter.
 *
 * @return {Array} filtered repository list
 */
function filterRepositories() {
    if (!repositories) return [];

    const filterValue = document.getElementById("filter").value;
    const filterRegex = new RegExp(filterValue, "i");

    return repositories.filter((repo) => filterRegex.test(repo.name));
}


/**
 * Displays the repository list in a table.
 *
 * @param {Array} repositories - repository list to display
 */
function viewRepositories(repositories) {
    const repositories_dom = document.getElementById("repositories");
    if (!repositories_dom) return;

    new Table({
        element: repositories_dom,
        headers: {
            name: {
                format: (name, image) => {
                    const match = name.match(/^(.*)\/(.*)$/);
                    const a = document.createElement("a");
                    a.href = `/_/${image.name}`;
                    a.className = "text-decoration-none text-nowrap fw-bold";
                    a.textContent = match ? match[2] : name;

                    const mark = imageMark(image.name);
                    const badge = markToBadge(mark, {
                        tooltip: { "data-bs-placement": "right" },
                        text: "",
                    });

                    const name_div = document.createElement("div");
                    name_div.appendChild(a);
                    name_div.appendChild(badge);

                    const flex_div = document.createElement("div");
                    flex_div.className = "row small text-nowrap text-muted";

                    const repo_div = document.createElement("div");
                    repo_div.className = "col-5 col-md-12 pe-none text-truncate pe-0";
                    repo_div.textContent = image.name;
                    flex_div.appendChild(repo_div);

                    if (image.size) {
                        const size_div = document.createElement("div");
                        size_div.className = "col-3 text-center d-md-none text-truncate p-0";
                        size_div.textContent = sizeFormat(image.size);
                        flex_div.appendChild(size_div);
                    }

                    if (image.created) {
                        const created_div = document.createElement("div");
                        created_div.className = "col-4 text-end d-md-none text-truncate ps-0";
                        created_div.appendChild(lastModified(image.created));
                        flex_div.appendChild(created_div);
                    }

                    const div = document.createElement("div");
                    div.appendChild(name_div);
                    div.appendChild(flex_div);
                    return div;
                },
                width: 400
            },
            repository: {
                width: "auto",
                format: (repository) => {
                    const a = document.createElement("a");
                    a.href = `/r/${repository}`;
                    a.className = "text-body text-nowrap";
                    a.textContent = repository;
                    return a;
                }
            },
            tags: {
                display: repositories.length && "tags" in repositories[0],
                width: 200
            },
            size: {
                display: repositories.length && "size" in repositories[0],
                width: 200,
                format: (size) => sizeFormat(size)
            },
            created: {
                display: repositories.length && "created" in repositories[0],
                width: 200,
                format: (timestamp) => lastModified(timestamp)
            },
        },
        data: repositories,
        className: "table table-sm table-hover align-middle",
        theadClassName: "table table-sm",
        empty: " ",
        sort: true,
        limit: images_per_page,
        undefined_headers: true,
        redraw_bind: () => tooltip()
    }).view();
}


/**
 * Fetches and displays the broadcast message.
 */
function viewBroadcast() {
    if (!broadcast_exists) return;

    const broadcastTitle = document.getElementById("broadcast_title");
    const broadcast = document.getElementById("broadcast");

    $.ajax({
        url: `/broadcast`,
        type: "GET",
        cache: false,
        async: true,
        success: function (raw) {
            if (!raw) return;

            const converter = new showdown.Converter({
                tables: true,
                tasklists: true,
                simplifiedAutoLink: true
            });

            broadcast.innerHTML = converter.makeHtml(raw);
            broadcastTitle.innerText = broadcast.innerText.split("\n")[0];
            hljs.highlightAll();
        }
    });
}
