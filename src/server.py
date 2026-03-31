"""
The server implemented here is not fully separated from the functionality of
the website. I.e. the server knows what the website does, though it does not
know how it does it.
The abstraction structure is the following
server.py (pathing and appropriate response function calls)
|> runner.py (implements the response functions. I.e. knows how to response to
              specific path GET or POST requests)
    |> auswertung.py (Holds the logic which creates the data structure for the
                      graph)
    |> other auxiliary modules like logger and benchmark_timer
"""


from rcssmin import cssmin
from rjsmin import jsmin
import os
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import json
from grundform import grundform
from logger import log, LogType
from runner import fill_missing_data_with_config_defaults, label_new_text_
from runner import process_request, train_the_model, get_label_list, startup

from runner import CONFIG_FILE_PATH_GRAPHS, CONFIG_FILE_PATH_GRUNDFORM


class Handler(BaseHTTPRequestHandler):

    def _respond_with_body(self, body, content_type):
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _respond_with_static_file(self, path, content_type):
        self.send_response(200)
        self.send_header("Content-type", content_type)
        self.end_headers()

        with open(path[1:], 'rb') as file:
            if content_type == "text/css":
                self.wfile.write(cssmin(file.read()))  # type: ignore
            elif content_type == "text/javascript":
                self.wfile.write(jsmin(file.read()))  # type: ignore
            else:
                self.wfile.write(file.read())  # Send

    def do_GET(self):

        path = self.path
        content_type = "text/html; charset=utf-8"

        if path == "/":
            path = "/static/index.html"

        if path == "/graph":
            path = "/static/graph.html"

        if path == "/erthaos":
            path = "/static/erthaos.html"

        if path == "/grundform":
            path = "/static/grundform.html"

        # file based routing for paths that start with static
        elif path.startswith("/static/"):
            if path.endswith(".css"):
                content_type = "text/css"
            elif path.endswith(".html"):
                content_type = "text/html; charset=utf-8"
            elif path.endswith(".js"):
                content_type = "text/javascript"
            else:
                return

        elif path == "/favicon.ico":
            path = "/static/KF.jpg"
            content_type = "image/x-icon"

        # dynamically loading the vis library for the graph visualization
        elif path.startswith("/lib/"):
            if path.endswith("js"):
                content_type = "text/javascript"
            elif path.endswith("css"):
                content_type = "text/css"
            else:
                content_type = ""
        else:
            return

        self._respond_with_static_file(path, content_type)

    def _send_response(self, res, err, status_code: int = 200):

        response = json.dumps({"res": res, "err": err}).encode('utf-8')
        resp_len = str(len(response)) if response is not None else '0'
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Content-Length', resp_len)
        # allow CORS for testing (remove in production or restrict origin)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        if response is not None:
            self.wfile.write(response)

    def _basic_form_handling(self):
        length = int(self.headers.get('Content-Length', 0))
        incomming_payload = self.rfile.read(length).decode('utf-8')

        try:
            data = json.loads(incomming_payload)
            return data
        except Exception as e:
            # fallback: return a json object with raw body
            log(f"Could not parse {incomming_payload=}. Caught the following exception: {e} ",
                context="do_POST",
                log_type=LogType.Error)
            return

    def _update_graph(self):
        data = self._basic_form_handling()
        if data is None:
            err = 'Wrong data was provided!'
            self._send_response(None, err)
            return

        config = fill_missing_data_with_config_defaults(
            data, CONFIG_FILE_PATH_GRAPHS)
        if config is None:
            self._send_response(None, None, status_code=500)
            return

        nodes, edges = process_request(config)
        data = {"nodes": nodes, "edges": edges}
        self._send_response(data, None)

    def _labler_get_gesep_list(self):
        data = self._basic_form_handling()
        if data is None:
            err = 'Wrong data was provided!'
            self._send_response(None, err)
            return

        response = get_label_list(data)
        self._send_response(response, None)

    def _labler_train_on_labled_text(self):
        data = self._basic_form_handling()
        if data is None:
            err = 'Wrong data was provided!'
            self._send_response(None, err)
            return

        try:
            pos_coef, pos_features = train_the_model(data)
            res = {"pos_coef": pos_coef, "pos_features": pos_features}
            self._send_response(res, None)
        except ValueError as e:
            err = f"Training fehlgeschlagen wegen Python Error: {e}"
            log(err, context='_labler_train_on_labled_text',
                log_type=LogType.Error)
            self._send_response(None, err)

    def _label_new_text(self):
        data = self._basic_form_handling()
        if data is None:
            err = 'Wrong data was provided!'
            self._send_response(None, err)
            return

        try:
            sorted_similarities_unlab, quelle, inhalt = label_new_text_(data)

            response = {
                "sorted_similarities_unlabeled": sorted_similarities_unlab,
                "quelle": quelle,
                "inhalt": inhalt
            }

            self._send_response(response, None)

        except ValueError as e:
            err = f"Vorhersage fehlgeschlagen wegen Python Error: {e}"
            log(err, context=__name__, log_type=LogType.Error)
            self._send_response(None, err)

    def _grundform_request(self):
        data = self._basic_form_handling()
        if data is None:
            err = 'Wrong data was provided!'
            self._send_response(None, err)
            return

        try:

            config = fill_missing_data_with_config_defaults(
                data, CONFIG_FILE_PATH_GRUNDFORM)

            def list_of_dicts_to_dict(lod):
                ret = dict()
                for el in lod:
                    ret[el["name"]] = el["value"]
                return ret

            params = list_of_dicts_to_dict(config)

            response = grundform(params)

            self._send_response(response, None)

        except ValueError as e:
            err = f"Vorhersage fehlgeschlagen wegen Python Error: {e}"
            log(err, context=__name__, log_type=LogType.Error)
            self._send_response(None, err)

    def do_POST(self):
        if self.path == "/update_graph":
            self._update_graph()
            return

        if self.path == "/labler_get_gesep_list":
            self._labler_get_gesep_list()
            return

        if self.path == "/labler_train_on_labled_text":
            self._labler_train_on_labled_text()
            return

        if self.path == "/label_new_text":
            self._label_new_text()
            return

        if self.path == "/grundform_request":
            self._grundform_request()
            return


def main():
    pid = os.getpid()
    log("!!!!!!!!!!!!!!!!!!!!!! START  !!!!!!!!!!!!!!!!!!!!!!!!!",
        context='main')
    log(f"running a server with pid {pid}", context='main')

    startup()
    with ThreadingHTTPServer(("0.0.0.0", 8080), Handler) as server:
        server.serve_forever()


if __name__ == "__main__":
    main()
