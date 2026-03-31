# Assistent für die automatische Erkennung der gesuchten Motive

# Anpassbare Variablen:

"""
Sprache: Filter für die Sprache des Texte. Entspricht dem Attributwert des
         Elements //langUsage/anguage/@ident="" in der XML Datei.

gesuchte_episoden = []: Die Abfragewerte für das Zielmotiv mit entsprechende Label.
                        Die Werte von 'gesuchte_episoden können nach der in der
                        Motivliste ausgewälte Zeilen, oder ihre Bestandteilen ausgefült
                        werden und anschließend in der Anfragezeile als Anfrage mit
                        'or' und/oder 'and' Opperatoren bestimmen.

Stoppwortliste für die bestimmte Sprache.
"""

# Alle Abhängigkeiten importieren
from io import StringIO
import nltk
# Importieren der ElementTree-Bibliothek zum Parsen von XML
import xml.etree.ElementTree as ET
import numpy as np
import pandas as pd

from hilfsfunktoinen import create_logistic_regression_model, find_similar, load_json_safely
from hilfsfunktoinen import feature_set_selection
from hilfsfunktoinen import gesuchte_episoden_labeln
from hilfsfunktoinen import parse_xml
from hilfsfunktoinen import lade_referenz_liste_aus_xsd
from sklearn.feature_extraction.text import TfidfVectorizer


def get_root_node(xml_database_name):
    return ET.parse(xml_database_name).getroot()


NS = {'tei': 'http://www.tei-c.org/ns/1.0'}  # 3 Namespace definieren
# Beispiel: Referenzliste laden
REFERENZ_LISTE = lade_referenz_liste_aus_xsd(
    "kf/vmf_d1.xsd")  # passe den Pfad an

PARAM_NGRAMM_RANGE = (1, 1)
PARAM_MIN_DF = 2
# ausgabe parameter
PARAM_PRINT_CUTOFF = 0.5
SONDERZEICHEN_CONFIG_PATH = "configs/sonderzeichen_config.json"


# GLOBAL STATE

USED_STOPWORDS = dict()  # type: ignore

SPECIAL_CHARACHTER_DICT = dict()  # type: ignore
BASE_STOPWORDS_DICT = dict()  # type: ignore
SPECIAL_CHARACHTERS_AND_BASE_STOPWORDS_JSON = load_json_safely(
    SONDERZEICHEN_CONFIG_PATH, safe_return=[{}])

DEFAULT_SPECIAL_CHARACHTERS = [
    ("|", ""), (":", ""), ("ä", "ae"), ("ü", "ue"), ("ö", "oe"),
    ("ß", "ss"), (",", ""), ("\n", " "), ("'", ""), ("…", ""),
    ("\"", ""), ("*", ""), ("(", ""), (")", ""), ("-", ""), (".", ""),
    ("?", ""), ("!", ""), ("„", ""), ("+", ""), ("=", ""), ("_", ""),
    ("­", ""), ("“", ""), ("”", ""), (";", ""), ("~", ""), ("`", ""),
    ("«", ""), ("»", ""), ("|", ""), ("]", ""), ("[", "")
]


def get_special_charachter_list(language):

    if language in SPECIAL_CHARACHTER_DICT.keys():
        return SPECIAL_CHARACHTER_DICT[language]
    else:
        for el in SPECIAL_CHARACHTERS_AND_BASE_STOPWORDS_JSON:
            if el["language"] == language:
                SPECIAL_CHARACHTER_DICT[language] = el["sonderzeichen"]
                return SPECIAL_CHARACHTER_DICT[language]
    return DEFAULT_SPECIAL_CHARACHTERS


def get_base_stopwords_list(language):

    if language in BASE_STOPWORDS_DICT.keys():
        return BASE_STOPWORDS_DICT[language]
    else:
        for el in SPECIAL_CHARACHTERS_AND_BASE_STOPWORDS_JSON:
            if el["language"] == language:
                BASE_STOPWORDS_DICT[language] = el["base_stopwords"]
                return BASE_STOPWORDS_DICT[language]
    return []


def parse_xml_into_dataframe(xml_database_name, special_charachters):
    # gelabelte XML daten parsen und dataframe erstellen
    maerchen = parse_xml(get_root_node(xml_database_name),
                         NS, REFERENZ_LISTE, special_charachters, parse_labels=True)
    # xml header
    maerchen_header = 'quelle,index_string,inhalt,index_binar'
    maerchen = f'{maerchen_header}\n{maerchen}'
    df_maerchen = pd.read_csv(StringIO(maerchen)).dropna()
    return df_maerchen


def get_stopwords(stopwords_sprache):

    custom_stop_word_list = get_base_stopwords_list(stopwords_sprache)
    if stopwords_sprache in USED_STOPWORDS:
        custom_stop_word_list = USED_STOPWORDS[stopwords_sprache]
    else:
        nltk.download('stopwords')
        nltk_stop_words_list = nltk.corpus.stopwords.words(stopwords_sprache)
        custom_stop_word_list = custom_stop_word_list + nltk_stop_words_list
        USED_STOPWORDS[stopwords_sprache] = custom_stop_word_list

    return custom_stop_word_list


def model_training(gesep_list, selected_episode_opt, stopwords_sprache, df_maerchen):
    gesuchte_episoden_labeln(gesep_list, df_maerchen)
    # ncht gewollte labela eliminieren

    if selected_episode_opt is not None:
        # Datensätzen die diesen a Wert nicht haben aber b und/oder c Werte besitzen können, werden aus der Aggregatiodatei
        # eliminiert. Dadurch wird es verhindert, dass die Datensetzen mit gleichen Inhalte nicht als negative Werte entgegengesetzt werden.
        # Zeilen mit index_binar = 1 entfernen, wenn index_string nicht "a000" enthält PARAM_elim = "a425"

        df_maerchen = df_maerchen[~(
            (df_maerchen['index_binar'] == 0) &
            (~df_maerchen['index_string'].str.contains(
                selected_episode_opt, na=False))
        )
        ]

    X_train: pd.Series = df_maerchen.inhalt
    y_train: pd.Series = df_maerchen.index_binar

    custom_stop_word_list = get_stopwords(stopwords_sprache)

    model_tfidf_logreg = create_logistic_regression_model(X_train, y_train,
                                                          PARAM_MIN_DF,
                                                          custom_stop_word_list,
                                                          PARAM_NGRAMM_RANGE,
                                                          perform_regularization_sweep=False)

    feature_names = np.array(
        model_tfidf_logreg.named_steps["tfidfvectorizer"].get_feature_names_out())
    coefficients = model_tfidf_logreg.named_steps["logisticregression"].coef_[
        0]

    pos_coef, pos_features = feature_set_selection(coefficients, feature_names)
    return pos_coef, pos_features


def label_new_text(xml_database_name, stopwords_sprache, special_charachters,
                   coef_cutoff,  pos_coef, pos_features):

    selected_features = pos_features[pos_coef > coef_cutoff]
    custom_stop_word_list = get_stopwords(stopwords_sprache)
    vectorizer = TfidfVectorizer(analyzer='word', min_df=PARAM_MIN_DF,
                                 stop_words=custom_stop_word_list,
                                 ngram_range=PARAM_NGRAMM_RANGE)

    selected_features_text = " ".join(selected_features)

    maerchen_nicht_gelabelt = parse_xml(get_root_node(
        xml_database_name), NS, REFERENZ_LISTE, special_charachters, parse_labels=False)

    maerchen_nicht_gelabelt_header = 'quelle,inhalt,index_binar'
    maerchen_nicht_gelabelt = (
        f'{maerchen_nicht_gelabelt_header}\n{maerchen_nicht_gelabelt}')
    df_maerchen_nicht_gelabelt = pd.read_csv(
        StringIO(maerchen_nicht_gelabelt)).dropna()

    t_corpus = df_maerchen_nicht_gelabelt['inhalt'].to_list()
    t_corpus.append(selected_features_text)

    all_coef_vector_unlabeled = vectorizer.fit_transform(t_corpus)

    model_vector_unlabeled = all_coef_vector_unlabeled[-1]
    result_coefs = all_coef_vector_unlabeled[:-1]

    sorted_index_unlabeled, sorted_similarities_unlabeled = find_similar(
        model_vector_unlabeled, result_coefs)
    sorted_similarities_unlabeled = np.round(sorted_similarities_unlabeled, 5)

    return sorted_similarities_unlabeled.tolist(), df_maerchen_nicht_gelabelt['quelle'].iloc[sorted_index_unlabeled].to_list(), df_maerchen_nicht_gelabelt['inhalt'].iloc[sorted_index_unlabeled].to_list()
