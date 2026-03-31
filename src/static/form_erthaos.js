REQUEST_IN_FLIGHT = false

globalThis.AppState = {
    form1_data: null,
    form2_data: null,
    original_text: '',
    coeff_cutoff: 0,
    pos_coefs: null,
    pos_features: null
}

function filterText() {

    const input = document.getElementById('search').value.toLowerCase();

    original_text = AppState.original_text

    if (!input) { return }

    const textArea = document.getElementById('episodeLabelsText');

    new_text = ''
    original_text.split('\n').forEach(line => {
        if (line.toLowerCase().includes(input) && input) {
            new_text += line + '\n'
        }
    })
    regexp = new RegExp(input, 'gi')
    textArea.innerHTML = new_text.replace(regexp, "<mark>$&</mark>")

}

async function server_request(target, bodyJson) {
    const res = await fetch(target, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(bodyJson)
    });

    if (!res.ok) {
        throw new Error('Generic Error. Network response not OK: ' + res.status);
    }

    let resp = await res.json()
    if (resp.err != null) {
        const server_error = resp.err;
        throw new Error('Server Error: ' + server_error);
    }
    return resp
}

// Add mouse move event listener
(function() {

    function plot_chart(values) {

        AppState.coeff_cutoff = 0.3 * values[0]

        let lineHeight = AppState.coeff_cutoff;
        const layout = function(lineHeight) {
            return {
                shapes: [{
                    type: 'line',
                    x0: -0.5, // Starting x position for the line
                    x1: values.length - 0.5, // Ending x position for the line
                    y0: lineHeight,
                    y1: lineHeight,
                    line: {
                        color: 'red',
                        width: 2,
                        dash: 'dash'
                    }
                }],
                title: 'Bar Chart with Movable Line',
                xaxis: { title: 'Categories' },
                yaxis: { title: 'Values' }
            }
        };

        const config = { responsive: true };

        const data = [
            {
                y: values,
                type: 'bar'
            }
        ]

        image = document.getElementById('visualization');


        Plotly.newPlot(image, data, layout(lineHeight), config);

        image.on('plotly_click', function(data) {
            height = lineHeight
            for (var i = 0; i < data.points.length; i++) {
                height = data.points[i].y.toPrecision(4)
            }

            AppState.coeff_cutoff = height
            Plotly.relayout(image, layout(height))
        });

    }

    async function final_handler(bodyJson) {

        const res = await server_request('/label_new_text', bodyJson)

        const server_response = res.res;

        outputDiv = document.getElementById('finalText')

        sorted_similarities_unlabeled = server_response['sorted_similarities_unlabeled']
        quelle_vec = server_response['quelle']
        inhalt_vec = server_response['inhalt']

        let output = '';

        for (let i = 0; i < sorted_similarities_unlabeled.length; i++) {
            let bewertung = sorted_similarities_unlabeled[i];
            let quelle = quelle_vec[i];
            let inhalt = inhalt_vec[i];

            output += `${bewertung.toFixed(4).padStart(9)} || ${quelle} ||  ${inhalt}<br>`;
        }

        outputDiv.innerHTML = output;

    }

    async function training_handler(bodyJson) {
        const res = await server_request('/labler_train_on_labled_text', bodyJson)

        const server_response = res.res;

        textArea = document.getElementById('positiveFeaturesText')

        words = server_response["pos_features"].reverse()
        pos_coef = server_response["pos_coef"].reverse()

        word_string = '' // words.join(' ');
        words.forEach((word, index) => {
            // Create a new line with the index and the word
            const line = `${index + 1}.&nbsp;${word}\n`;
            word_string = word_string.concat(line)
        });

        textArea.innerHTML = word_string

        AppState.pos_coefs = pos_coef
        AppState.pos_features = words

        plot_chart(pos_coef)

        document.getElementById('label-new-text').classList.remove('invisible');
    }

    async function get_labels_handler(bodyJson) {

        const res = await server_request('/labler_get_gesep_list', bodyJson)

        const server_response = res.res;

        textArea = document.getElementById('episodeLabelsText')
        AppState.original_text = server_response;
        textArea.innerHTML = server_response

    }

    async function handle_button_press(btn, body, handler) {

        original_buton_text = btn.textContent;

        try {
            REQUEST_IN_FLIGHT = true;
            btn.disabled = true;
            btn.textContent = "waiting...";
            console.log("awaiting")
            await handler(body);
        } catch (err) {
            alert('Error: ' + err.message);
        } finally {
            REQUEST_IN_FLIGHT = false;
            btn.disabled = false;
            btn.textContent = original_buton_text;
        }
    }


    xml_selector_form = document.getElementById('xmlSelectorForm');
    xml_selector_form.addEventListener('submit', async (e) => {
        e.preventDefault();

        if (REQUEST_IN_FLIGHT) return;

        form_data = new FormData(e.target).entries();
        filtered_data = Array.from(form_data).filter(([_, v]) => String(v).trim() !== '')
        const body = Object.fromEntries(filtered_data)
        AppState.form1_data = body

        const get_labels_btn = document.getElementById('get-labels');
        handle_button_press(get_labels_btn, body, get_labels_handler)

    });


    episode_selector_form = document.getElementById('episodeSelectorForm');
    episode_selector_form.addEventListener('submit', async (e) => {
        e.preventDefault();

        if (REQUEST_IN_FLIGHT) return;

        form_data = new FormData(e.target).entries();
        filtered_data = Array.from(form_data).filter(([_, v]) => String(v).trim() !== '')
        const body = Object.fromEntries(filtered_data)
        AppState.form2_data = body
        extended_body = { ...(AppState.form1_data), ...(AppState.form2_data) }

        const btn = document.getElementById('select-labels');
        handle_button_press(btn, extended_body, training_handler)
    });

    labler_btn = document.getElementById('label-new-text')
    labler_btn.addEventListener('click', async (e) => {
        if (REQUEST_IN_FLIGHT) return;
        const { original_text: _, ...bodyJson } = AppState;
        handle_button_press(labler_btn, bodyJson, final_handler)
    })

    // optional: auto-load on page open with default form values
})()
