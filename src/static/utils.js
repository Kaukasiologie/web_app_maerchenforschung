function validateForm() {
    const inputs = document.querySelectorAll('input[type="number"], input[type="text"]');
    let isValid = true;

    inputs.forEach(input => {

        const errorElement = document.getElementById(input.name + "-error");

        if (errorElement === null) return;

        if (input.value.trim() === "") {
            errorElement.textContent = "Dieses Feld ist erforderlich.";
            isValid = false;
        } else {
            errorElement.textContent = ""; // Clear the message
        }
    });

    return isValid;
}

function filterText(input, textArea, original_text) {

    if (!input) { return }

    input = input.toLowerCase()
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

async function handle_button_press(btn, body, handler) {

    original_buton_text = btn.textContent;

    try {
        REQUEST_IN_FLIGHT = true;
        btn.disabled = true;
        btn.textContent = "waiting...";
        console.log("awaiting")
        await handler(body);
    } catch (err) {

        const msg = 'Error: ' + err.message
        const error_element = document.getElementById("text-area-error")
        error_element.classList.remove('invisible')
        error_element.textContent = msg

    } finally {
        REQUEST_IN_FLIGHT = false;
        btn.disabled = false;
        btn.textContent = original_buton_text;
    }
}
