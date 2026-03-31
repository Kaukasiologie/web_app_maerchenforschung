from collections import defaultdict
from itertools import combinations
from pyvis.network import Network # type: ignore
import pandas as pd
import xml.etree.ElementTree as ET

from logger import log, LogType


# ============================================
# Märchenanalyse mit Graph-Erstellung (pyvis)
# und Hervorhebung eines bestimmten Knotens
# ============================================

def read_xml_into_df(datei: str):
    '''
     TEI-XML-Datei einlesen und CSV erzeugen
    '''
    tree = ET.parse(datei)
    root_node = tree.getroot()
    NS = {'tei': 'http://www.tei-c.org/ns/1.0'}

    labelas = []
    labelxs = []

    for corp in root_node.findall(".//tei:teiCorpus", NS):
        for tei in corp.findall("tei:TEI", NS):
            for ganze in tei.findall(".//tei:text", NS):
                labelx = ganze.attrib['{http://www.w3.org/XML/1998/namespace}id']
                for body in ganze.findall(".//tei:body", NS):
                    for absatz in body.findall(".//tei:p", NS):
                        for phrase in absatz.findall(".//tei:seg", NS):
                            labela = phrase.attrib['{www.dglab.uni-jena.de/vmf/a}ana']
                            if labela.startswith('a'):
                                labelas.append(labela)
                                labelxs.append(labelx)

    df = pd.DataFrame({"labela": labelas, "labelx": labelxs})
    df.drop_duplicates(inplace=True)
    return df


def read_csv(filename: str):
    with open(filename, 'w', encoding='utf-8') as f:
        csv_formatted_string = f.read()
    return csv_formatted_string


def get_node_size(frequency, frequency_dict, min_size=10, max_size=50):
    '''
        Knotengröße skalieren
    '''
    max_frequency = max(frequency_dict.values()) if frequency_dict else 1
    return min_size + (max_size - min_size) * (frequency / max_frequency)


def get_display_label(label, show_full_labels: bool, replacement_dict: dict):
    """
    Gibt entweder nur die Typnummer oder den vollständigen Labeltext zurück.
    `show_full_labels` Auf False setzen, um nur Typnummern (z. B. a300) zu
    zeigen.
    """
    if show_full_labels:
        return replacement_dict.get(label, label)
    else:
        return label


def do_all(maerchen_df, i_gesuchter_knoten: str, i_min_node_weight: int,
           i_min_edge_weight: int,
           i_show_full_label: bool):

    # ------------------------------------------------
    # Graph-Daten aus CSV laden
    # ------------------------------------------------
    net = Network()

    edges  = dict() # type: ignore[var-annotated]
    self_loops = dict() # type: ignore[var-annotated]
    node_frequency_ = defaultdict(set)

    # ------------------------------------------------
    # XSD einlesen für Bezeichnungs-Ersetzungen
    # ------------------------------------------------
    xsd_path = 'kf/vmf_a.xsd'
    tree = ET.parse(xsd_path)
    root = tree.getroot()
    ns = {'xs': 'http://www.w3.org/2001/XMLSchema'}

    replacement_dict = {}
    for enumeration in root.findall(".//xs:enumeration", ns):
        value = enumeration.attrib.get('value', '')
        if ' ' in value:
            split_value = value.split(' ', 1)
            key = split_value[0]
            replacement_dict[key] = value

    # ------------------------------------------------
    # Kanten und Häufigkeiten berechnen
    # ------------------------------------------------
    for labelx, group in maerchen_df.groupby('labelx'):
        labelas = group['labela'].unique()

        if len(labelas) == 1:
            labela = labelas[0]
            if labela in self_loops:
                self_loops[labela]['weight'] += 1 # type: ignore
                self_loops[labela]['labelx_values'].append(labelx) # type: ignore
            else:
                self_loops[labela] = {'weight': 1, 'labelx_values': [labelx]}
            node_frequency_[labela].add(labelx)
        else:
            for pair in combinations(labelas, 2):
                sorted_pair = tuple(sorted(pair))
                if sorted_pair in edges:
                    edges[sorted_pair]['weight'] += 1 # type: ignore
                    edges[sorted_pair]['labelx_values'].append(labelx) # type: ignore
                else:
                    edges[sorted_pair] = { 'weight': 1, 'labelx_values': [labelx]}
                node_frequency_[pair[0]].add(labelx)
                node_frequency_[pair[1]].add(labelx)

    node_frequency = {node: len(labelx_set)
                      for node, labelx_set in node_frequency_.items()}

    # ------------------------------------------------
    # Knoten & Kanten hinzufügen
    # ------------------------------------------------
    for (labela1, labela2), data in edges.items():
        edge_weight: int = data['weight'] # type: ignore

        if edge_weight < i_min_edge_weight:
            continue

        nf_a1: int = node_frequency[labela1]
        nf_a2: int = node_frequency[labela2]

        if (nf_a1 <= i_min_node_weight) or (nf_a2 <= i_min_node_weight):
            continue

        title1 = replacement_dict.get(labela1, labela1)
        title2 = replacement_dict.get(labela2, labela2)
        size1 = get_node_size(nf_a1, node_frequency)
        size2 = get_node_size(nf_a2, node_frequency)

        # nzeige-Label je nach Einstellung wählen
        display_label1 = get_display_label(labela1,  i_show_full_label, replacement_dict)
        display_label2 = get_display_label(labela2, i_show_full_label, replacement_dict)

        net.add_node(labela1, label=display_label1, title=f'{title1} ({nf_a1})', size=size1)
        net.add_node(labela2, label=display_label2, title=f'{title2} ({nf_a2})', size=size2)
        net.add_edge(labela1, labela2, value=edge_weight, title=f'{edge_weight}')


    for labela, data in self_loops.items():
        if node_frequency[labela] <= i_min_node_weight:
            continue
        title = replacement_dict.get(labela, labela)
        size = get_node_size(node_frequency[labela], node_frequency)

        # Anzeige-Label je nach Einstellung wählen
        display_label = get_display_label(labela, i_show_full_label, replacement_dict)

        net.add_node(labela, label=display_label, title=f'{title} ({node_frequency[labela]})', size=size)
        net.add_edge(labela, labela, value=data['weight'], title=f'{data["weight"]}')

    # ------------------------------------------------
    # Gesuchten Knoten hervorheben
    # ------------------------------------------------
    found = False
    if i_gesuchter_knoten == '':
        return net.nodes, net.edges

    for node in net.nodes:
        if node["id"] == i_gesuchter_knoten:
            found = True
            node["color"] = "red"
            log(f"Knoten '{i_gesuchter_knoten}' gefunden und hervorgehoben.", "do_all")
            break

    if not found:
        log(f"Knoten '{i_gesuchter_knoten}' wurde im Graphen nicht gefunden.", "do_all", log_type=LogType.Error)

    return net.nodes, net.edges
