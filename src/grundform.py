import json
from hilfsfunktoinen import sortiere_dana, lade_referenz_liste_aus_xsd

from collections import Counter, defaultdict, deque
import xml.etree.ElementTree as ET


# --- Beispiele ---
# nur EINZELTYP ohne Kombination = Knoten mit Bogen
# Typ = "a707"

# Kombination : Knoten mit Bogen und/oder Kanten mit der Möglichkeit Kanten zu
# filtrieren
# Typ = {"AND": ["a563","a425A"], "OR": ["a300"], "NOT": ["a700"], "MODE": "OR"}
# Typ = {"AND": ["a563","a425A"], "OR": ["a300"], "MODE": "AND"}


# Falls Typ als Liste übergeben → automatisch zu {"AND": [...]} umwandeln


def get_mode(Typ):
    if isinstance(Typ, list):
        Typ = {"AND": Typ}

    # Standard-Mode, falls nicht angegeben
    mode = Typ.get("MODE", "AND").upper() if isinstance(Typ, dict) else "AND"
    return mode


def eindeutige_zeilen_erstellen(xml_database_name, typ_input, min_count):

    min_count = int(min_count)
    typ_input = json.loads(typ_input)

    NS = {'tei': 'http://www.tei-c.org/ns/1.0'}
    ROOT_NODE = ET.parse(f"xml_sources/{xml_database_name}").getroot()

    mode = get_mode(typ_input)
    REFERENZ_LISTE = lade_referenz_liste_aus_xsd("kf/vmf_d1.xsd")

    textid_to_typ = {}
    for corp in ROOT_NODE.findall(".//tei:teiCorpus", NS):

        for ganze in corp.findall(".//tei:TEI", NS):

            for text in ganze.findall(".//tei:text", NS):
                text_xmlid = text.attrib.get(
                    '{http://www.w3.org/XML/1998/namespace}id', '')

                types_all = set()
                for segm in text.findall(".//tei:seg", NS):
                    tn = segm.attrib.get(
                        '{www.dglab.uni-jena.de/vmf/a}ana', '')

                    tn_list = []
                    for x in tn.replace(";", ",").split(","):
                        x = x.strip()
                        if x.startswith('a'):
                            tn_list.append(x)

                    types_all.update(tn_list)

                if isinstance(typ_input, str):
                    # Nur ein einziger Typ erlaubt (keine Kombinationen)
                    ok = (types_all == {typ_input})
                else:
                    ok_and = True
                    ok_or = True
                    ok_not = True

                    if "AND" in typ_input:
                        ok_and = all(
                            t in types_all for t in typ_input["AND"])
                    if "OR" in typ_input:
                        ok_or = any(
                            t in types_all for t in typ_input["OR"])
                    if "NOT" in typ_input:
                        ok_not = all(
                            t not in types_all for t in typ_input["NOT"])

                    # Kombination nach MODE
                    if "AND" in typ_input and "OR" in typ_input:
                        if mode == "OR":
                            ok = (ok_and or ok_or) and ok_not
                        else:  # MODE = "AND" (Standard)
                            ok = (ok_and and ok_or) and ok_not
                    elif "AND" in typ_input:
                        ok = ok_and and ok_not
                    elif "OR" in typ_input:
                        ok = ok_or and ok_not
                    else:
                        ok = ok_not
                if ok:
                    textid_to_typ[text_xmlid] = True

    # --- Ergebnis als Python-Liste speichern ---
    text_ids = sorted(textid_to_typ.keys())

    # Speichern der Märchendaten für jedes `text_id`
    maerchen_daten = {text_id: [] for text_id in text_ids}

    def label_url(lbl):
        return f'{{www.dglab.uni-jena.de/vmf/{lbl}}}ana'

    for text_id in text_ids:
        for ganze in ROOT_NODE.findall(".//{http://www.tei-c.org/ns/1.0}text"):
            quelle = ganze.attrib['{http://www.w3.org/XML/1998/namespace}id']

            if text_id != quelle:
                continue
            for body in ganze.findall(".//{http://www.tei-c.org/ns/1.0}body"):
                for absatz in body.findall(".//{http://www.tei-c.org/ns/1.0}p"):
                    for phrase in absatz.findall(".//{http://www.tei-c.org/ns/1.0}seg"):
                        if phrase is None:
                            continue

                        try:
                            attrib = phrase.attrib
                            text = phrase.text
                            if text is None:
                                text = ""
                        except KeyError:
                            continue

                        labela = attrib[label_url('a')]
                        if not labela.startswith('a'):
                            continue

                        labelbs = []
                        labelcs = []
                        labelds = []
                        for i in range(1, 6):
                            labelbs.append(attrib.get(label_url(f'b{i}'), 'N'))
                            labelcs.append(attrib.get(label_url(f'c{i}'), 'N'))
                            labelds.append(attrib.get(label_url(f'd{i}'), 'N'))

                        dana = "_".join(labelds).replace("_N", "")

                        try:
                            labeld = sortiere_dana(dana, REFERENZ_LISTE)
                        except ValueError:
                            labeld = dana

                        for lb, lc in zip(labelbs, labelcs):
                            row = f"{labela}:{lb}:{lc}:{labeld}"
                            if ':N:' not in row:
                                maerchen_daten[text_id].append(row)

    unique_values_per_text_id = {}
    result_data_per_ch = {}
    gesamt_ergebnisse = {}

    for text_id, filtered_data in maerchen_daten.items():
        # Duplikate erkennen und kennzeichnen
        seen = {}
        for i, line in enumerate(filtered_data):
            if line not in seen:
                seen[line] = 0
            else:
                seen[line] += 1
                suffix = "_+" * seen[line]
                filtered_data[i] = f"{line}{suffix}"

        # Eindeutige Werte extrahieren
        unique_values = (line.split(':')[0] for line in filtered_data)
        unique_values_per_text_id[text_id] = unique_values
        result_data_per_ch[text_id] = filtered_data
        gesamt_ergebnisse[text_id] = filtered_data

    zeilen_counter = Counter()
    # Alle TXT-Dateien im Ordner durchgehen
    for lines in gesamt_ergebnisse.values():
        for line in lines:
            z = line.strip()
            if z:
                zeilen_counter[z] += 1

    # Zeilen, die mindestens min_counts-mal vorkommen
    eindeutige_zeilen: set = {zeile for zeile,
                              count in zeilen_counter.items() if count >= min_count}

    return gesamt_ergebnisse, eindeutige_zeilen, text_ids


# --- Paarweise Stimmen sammeln ---
def collect_pair_votes(base_lines, gesamt_ergebnisse):

    votes = defaultdict(int)
    base_set = set(base_lines)
    for lines in gesamt_ergebnisse.values():
        lines = [line for line in lines if line in base_set]
        for i in range(len(lines)):
            for j in range(i+1, len(lines)):
                a, b = lines[i], lines[j]
                votes[(a, b)] += 1

    return votes


# --- Mehrheitsgraph bauen ---
def build_majority_graph(base_lines, votes):
    graph = defaultdict(set)
    indegree = {line: 0 for line in base_lines}
    used_nodes = set()
    for (a, b), count in votes.items():
        reverse_count = votes.get((b, a), 0)
        if count > reverse_count:
            if b not in graph[a]:
                graph[a].add(b)
                indegree[b] += 1
                used_nodes.update([a, b])
        elif reverse_count > count:
            if a not in graph[b]:
                graph[b].add(a)
                indegree[a] += 1
                used_nodes.update([a, b])
    return graph, indegree, used_nodes


# --- Topologische Sortierung ---
def topo_sort(graph, indegree, used_nodes):
    queue = deque([n for n in used_nodes if indegree[n] == 0])
    result = []
    while queue:
        node = queue.popleft()
        if node not in result:
            result.append(node)
        for neighbor in graph[node]:
            indegree[neighbor] -= 1
            if indegree[neighbor] == 0:
                queue.append(neighbor)
    return result


# --- Basisdatei sortieren ---
def sort_base(eindeutige_zeilen, gesamt_ergebnisse):

    votes = collect_pair_votes(
        eindeutige_zeilen, gesamt_ergebnisse)

    graph, indegree, used_nodes = build_majority_graph(
        eindeutige_zeilen, votes)

    sorted_lines = topo_sort(graph, indegree, used_nodes)

    # Nicht verwendete Zeilen hinten anhängen + markieren
    for line in eindeutige_zeilen:
        if line not in sorted_lines:
            marked_line = f"*{line}"
            sorted_lines.append(marked_line)

    return sorted_lines


# --- Hauptprogramm ---
def grundform(data):

    min_count = int(data["min_count"])
    gesamt_ergebnisse, eindeutige_zeilen, text_ids = eindeutige_zeilen_erstellen(
        **data)

    # Sortierung nach Mehrheitsregeln
    sorted_lines = sort_base(sorted(eindeutige_zeilen), gesamt_ergebnisse)

    zeilen = []
    for i in range(0, len(text_ids), 3):
        zeilen.append("\t".join(f"'{w}'" for w in text_ids[i:i+3]))

    typ_formatiert = json.dumps(json.loads(data["typ_input"]))
    output_text = f'Typ(en) = {typ_formatiert}'
    output_text += "\n"
    output_text += f"Häufigkeit = {min_count}"
    output_text += "\n"
    output_text += "Text-IDs:"
    output_text += "\n"
    output_text += '\n'.join(zeilen)
    output_text += "\n---------------------\n"

    for line in sorted_lines:
        if line.startswith("*"):
            output_text += f"<b>{line}</b>\n"
        else:
            output_text += f"{line}\n"

    return output_text
