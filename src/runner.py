from typing import List, Dict
from pathlib import Path
from auswertung import read_xml_into_df, do_all
from hilfsfunktoinen import load_json_safely
from erthaos_ueberarbeitet import get_special_charachter_list, parse_xml_into_dataframe, model_training
from logger import log, LogType
from benchmark_timer import Timer
from erthaos_ueberarbeitet import label_new_text

import pandas as pd

TEMPLATES = Path("templates")
STATIC = Path("static")
STATIC.mkdir(exist_ok=True)

FAV_ICON = STATIC/'KF_L.png'

XML_SOURCES = Path("xml_sources")
XML_SOURCES.mkdir(exist_ok=True)

CONFIGS = Path("configs")

CONFIG_FILE_PATH_GRAPHS = CONFIGS/"default_forms_config.json"
CONFIG_FILE_PATH_LABLER = CONFIGS/"labler_default_forms_config.json"
CONFIG_FILE_PATH_GRUNDFORM = CONFIGS/"grundform_config.json"


def startup():
    make_graph_page("graph.html", CONFIG_FILE_PATH_GRAPHS)
    make_labler_page("erthaos.html", CONFIG_FILE_PATH_LABLER)
    make_grundform_page("grundform.html", CONFIG_FILE_PATH_GRUNDFORM)


def checkbox_to_bool(val):
    return val == 'on'


PARSED_XML_CACHE = dict()  # type: ignore


def process_request(config_file: list):

    config = {}
    for field in config_file:
        name = field["name"]
        value = field["value"]
        config[name] = value

    datei = f'xml_sources/{config["datei"]}'
    haeufigkeit = int(config["haeufigkeit"])
    min_edge_weight = int(config["min_edge_weight"])

    gesuchter_knoten = config["gesuchter_knoten"]

    display_full_name = checkbox_to_bool(config["show_full_name"])

    t1 = Timer("read xml")
    if datei in PARSED_XML_CACHE:
        maerchen_df = PARSED_XML_CACHE.get(datei)
    else:
        maerchen_df = read_xml_into_df(datei)
        PARSED_XML_CACHE[datei] = maerchen_df

    t1.stop()

    t2 = Timer("do all")
    nodes, edges = do_all(maerchen_df, gesuchter_knoten,
                          haeufigkeit, min_edge_weight, display_full_name)
    t2.stop()

    log(t1.human_readable_time(), context="process_request")
    log(t2.human_readable_time(), context="process_request")

    return nodes, edges


def _make_form(fields: List[Dict]):
    forms = []
    for field in fields:
        if not field["public"]:
            continue

        name = field["name"]
        label = field["label"]
        ftype = field["type"]
        required = field.get("required", False)
        info = field["info"]

        form_field = f"""<div class="form-field">
<br />
<label for="{name}" class="inline"> {label}</label>
<label class="info inline" data-tooltip="{info}">i</label>
"""

        if ftype == "select":
            form_field += f"""<select name="{name}">"""
            for value in field["value"]:
                form_field += f"""<option value="{value}">{value}</option>"""
            form_field += """</select>"""
        else:
            form_field += f"""
<input id="{name}" name="{name}" type="{ftype}"  />"""
            if required:
                form_field += f"""
<div id="{name}-error" class="error"></div>
</div>"""

        forms.append(form_field)

    form_str: str = '\n'.join(forms)
    return form_str


def render_static(name: Path):
    tpl = name.read_text(encoding="utf-8")
    return tpl.encode("utf-8")


def make_graph_page(template_name, config_name):
    fields = load_json_safely(config_name)

    tpl = (TEMPLATES / template_name).read_text(encoding="utf-8")
    body = tpl.replace("{{ forms }}", _make_form(fields))

    (STATIC / template_name).write_text(body, encoding="utf-8")


def make_labler_page(template_name, config_name):
    fields = load_json_safely(config_name, safe_return={})

    tpl = (TEMPLATES / template_name).read_text(encoding="utf-8")

    body1 = tpl.replace("{{ forms1 }}", _make_form(fields["xml_selection"]))
    body2 = body1.replace("{{ forms2 }}", _make_form(
        fields["episode_selection"]))

    (STATIC / template_name).write_text(body1, encoding="utf-8")
    (STATIC / template_name).write_text(body2, encoding="utf-8")


def make_grundform_page(template_name, config_name):
    fields = load_json_safely(config_name, safe_return=[{}])

    tpl = (TEMPLATES / template_name).read_text(encoding="utf-8")
    body = tpl.replace("{{ forms }}", _make_form(fields))

    (STATIC / template_name).write_text(body, encoding="utf-8")


ERTHAOS_LABLED_DATAFRAMES = dict()  # type: ignore


def parse_xml(xml_filename, language):

    special_chars = get_special_charachter_list(language)
    df_labeld = parse_xml_into_dataframe(
        f'xml_sources/{xml_filename}', special_chars)

    return df_labeld


def get_label_list(request_json):
    xml_filename = request_json['xml_database_name']

    config = load_json_safely(CONFIG_FILE_PATH_LABLER, None)
    if config is None:
        log("Bad config provided.", context="update")
        return None, None

    xml_selection_config = config['xml_selection']
    language_dict = get_element(xml_selection_config, 'language')

    if language_dict is None:
        log('Language could not be extracted from the configuration',
            context='train_the_model', log_type=LogType.Error)
        return None, None

    xml_language = language_dict['value'][xml_filename]

    df_labeld = parse_xml(xml_filename, xml_language)
    return '\n'.join(df_labeld['index_string'].to_list())


def train_the_model(request_json):

    config = load_json_safely(CONFIG_FILE_PATH_LABLER, None)
    if config is None:
        log("Bad config provided.", context="update")
        return None, None

    xml_selection_config = config['xml_selection']
    episode_selection_config = config['episode_selection']

    xml_selection_config = fill_missing_data_with_defaults(
        request_json, xml_selection_config)
    episode_selection_config = fill_missing_data_with_defaults(
        request_json, episode_selection_config)

    xml_database_name_field = get_element(xml_selection_config,
                                          'xml_database_name')

    if xml_database_name_field is None:
        log('xml_database_name_field is None',
            context='train_the_model', log_type=LogType.Error)
        return None, None

    xml_database_name = xml_database_name_field['value']

    language_dict = get_element(xml_selection_config, 'language')

    if language_dict is None:
        log('Language could not be extracted from the configuration',
            context='train_the_model', log_type=LogType.Error)
        return None, None

    stopwords_sprache = language_dict['value'][xml_database_name]
    gesep_raw = request_json['gesep']
    gesep_list = gesep_raw.split("|")

    selected_episode_opt = request_json.get('elim', None)
    df_maerchen = parse_xml(xml_database_name, stopwords_sprache)
    print(80 * '>')
    print(df_maerchen)
    print(80 * '<')

    pos_coef, pos_features = model_training(gesep_list, selected_episode_opt,
                                            stopwords_sprache, df_maerchen)

    return pos_coef.tolist(), pos_features.tolist()


def label_new_text_(data):
    xml_database_name = data["form1_data"]["xml_database_name"]
    xml_database_path = f'xml_sources/{xml_database_name}'

    stopwords_sprache = None
    fields = load_json_safely(CONFIG_FILE_PATH_LABLER, safe_return={})
    for element in fields["xml_selection"]:
        if (element["name"] == "language"):
            stopwords_sprache = element["value"][xml_database_name]

    import numpy as np

    coeff_cutoff = float(data["coeff_cutoff"])
    pos_coefs = np.array(data["pos_coefs"])
    pos_features = np.array(data["pos_features"])

    log(f"{xml_database_name=}")
    log(f"{coeff_cutoff=}")
    log(f"{pos_coefs=}")
    log(f"{pos_features=}")

    special_charachters = get_special_charachter_list(stopwords_sprache)
    sorted_similarities_unlabeled, quelle, inhalt = label_new_text(
        xml_database_path, stopwords_sprache, special_charachters,
        coeff_cutoff, pos_coefs, pos_features)
    return sorted_similarities_unlabeled, quelle, inhalt


def get_element(config, name):
    for field in config:
        if field['name'] == name:
            return field


def fill_missing_data_with_defaults(data, defaults):
    for field in defaults:
        name = field["name"]
        value = field["value"]
        new_value = data.get(name, value)
        if new_value != '':
            field["value"] = new_value

    return defaults


def fill_missing_data_with_config_defaults(data, config_file_name):
    config = load_json_safely(config_file_name, None)
    if config is None:
        log("Bad config provided.", context="update", log_type=LogType.Error)
        return None

    config = fill_missing_data_with_defaults(data, config)

    return config
