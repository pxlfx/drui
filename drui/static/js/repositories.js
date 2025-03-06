// image.js: getting and displaying a list of Docker images.

$(function () {
    const filter_dom = document.getElementById("filter");
    if (filter_dom) {
        filter_dom.onkeyup = () => {
            const filtered_data = filterRepositories();
            viewRepositories(filtered_data);
        };
        filter_dom.dispatchEvent(new Event('keyup'));
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

    return repositories.filter(repo => filterRegex.test(repo));
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
        headers: [
            {
                name: "application",
                format: ([app, image]) => `
                    <a href="/_/${image}" class="text-decoration-none text-nowrap fw-bold">${app}</a>
                    <div class="small text-muted text-nowrap pe-none">${image}</div>
                `,
                width: 400
            },
            {
                name: "repository",
                width: "auto",
                format: (repository) => `<a href="/r/${repository}" class="text-body text-nowrap">${repository}</a>`
            },
            {
                name: "mark",
                width: 200,
                display: official_prefix.length + verified_prefix.length > 0,
                format: mark => markToBadge(mark, {
                    tooltip: {
                        "data-bs-placement": "right"
                    }
                })
            }
        ],
        data: repositories.map((image) => {
            try {
                const match = image.match(/(?<repository>^.*)\/(?<application>.*)/).groups;
                return [[match.application, image], match.repository, imageMark(image)]
            } catch (error) {
                return [[image, image], " ", imageMark(image)]
            }
        }),
        className: "table table-sm table-hover align-middle",
        theadClassName: "thead-dark table-sm",
        empty: " ",
        sort: true,
        limit: images_per_page,
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
