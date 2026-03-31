(function() {

    // initialize empty network (keeps container ready)
    const container = document.getElementById('image');
    let network = null;
    const options = {
        physics: { stabilization: false },
        interaction: { hover: true },
        layout: { improvedLayout: false },
        nodes: { shape: 'dot', size: 36 },
        height: '100%',
        width: '100%'
    };

    async function loadAndRender(bodyJson) {
        const res = await fetch('/update_graph', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(bodyJson)
        });

        if (!res.ok) throw new Error('Network response not OK: ' + res.status);
        console.table(res)
        const response = await res.json();

        const serverJson = response.res

        const visNodes = new vis.DataSet(serverJson.nodes);
        const visEdges = new vis.DataSet(serverJson.edges);

        const data = { nodes: visNodes, edges: visEdges };

        if (!network) {
            network = new vis.Network(container, data, options);
        } else {
            network.setData(data);
        }

    }

    // form submit -> load graph

    in_flight = false
    data_form = document.getElementById('dataForm');
    data_form.addEventListener('submit', async (e) => {
        if (in_flight) return;

        e.preventDefault();

        form_data = new FormData(e.target).entries();
        filtered_data = Array.from(form_data).filter(([k, v]) => String(v).trim() !== '')
        const body = Object.fromEntries(filtered_data)

        const btn = document.getElementById('regenerate-button');
        original_buton_text = btn.textContent;
        try {
            in_flight = true;
            btn.disabled = true;
            btn.textContent = "waiting...";
            await loadAndRender(body);
        } catch (err) {
            document.getElementById('debug').textContent = 'Error: ' + err.message;
        } finally {
            in_flight = false;
            btn.disabled = false;
            btn.textContent = original_buton_text;
        }
    });

    // optional: auto-load on page open with default form values
    loadAndRender(Object.fromEntries(new FormData(document.getElementById('dataForm')).entries()))
        .catch(err => console.log('Auto-load error: ' + err.message));
})()
