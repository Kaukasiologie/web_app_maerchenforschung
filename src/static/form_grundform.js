REQUEST_IN_FLIGHT = false;

globalThis.AppState = {
    form_data: null,
    original_text: '',
    coeff_cutoff: 0,
    pos_coefs: null,
    pos_features: null
};

(function() {

    text_area = document.getElementById('grundform_script_result')

    async function request_handler(bodyJson) {

        const res = await server_request('/grundform_request', bodyJson)

        server_response = res.res;

        AppState.original_text = server_response;
        text_area.innerHTML = server_response

    }

    search_field = document.getElementById('search');
    search_field.addEventListener("input", async (_) => {
        filterText(search_field.value, text_area, AppState.original_text)
    })

    xml_selector_form = document.getElementById('xmlSelectorForm');
    xml_selector_form.addEventListener('submit', async (e) => {
        e.preventDefault();

        const error_element = document.getElementById("text-area-error")
        error_element.classList.add('invisible')

        if (!validateForm()) return;

        if (REQUEST_IN_FLIGHT) return;

        form_data = new FormData(e.target).entries();
        filtered_data = Array.from(form_data).filter(([_, v]) => String(v).trim() !== '')
        const body = Object.fromEntries(filtered_data)
        AppState.form_data = body

        const get_labels_btn = document.getElementById('get-labels');
        handle_button_press(get_labels_btn, body, request_handler)

    });

})()

