from hilfsfunktoinen import sortiere_dana, lade_referenz_liste_aus_xsd, sonderzeichen_entfernen

from collections import Counter, defaultdict, deque
import pandas as pd
import xml.etree.ElementTree as ET
import os


PARAM_SPRACHE = ""
PARAM_TEXT_ID = ""

OUTPUT_FOLDER = "GF/processed"
KORPUS = ""

# --- Beispiele ---
# nur EINZELTYP ohne Kombination = Knoten mit Bogen
# Typ = "a707"

# Kombination : Knoten mit Bogen und/oder Kanten mit der Möglichkeit Kanten zu filtrieren
# Typ = {"AND": ["a563","a425A"], "OR": ["a300"], "NOT": ["a700"], "MODE": "OR"}
# Typ = {"AND": ["a563","a425A"], "OR": ["a300"], "MODE": "AND"}


# Falls Typ als Liste übergeben → automatisch zu {"AND": [...]} umwandeln


def get_mode(Typ):
    if isinstance(Typ, list):
        Typ = {"AND": Typ}

    # Standard-Mode, falls nicht angegeben
    mode = Typ.get("MODE", "AND").upper() if isinstance(Typ, dict) else "AND"
    return mode


def eindeutige_zeilen_erstellen(xml_file, korpus, Typ, min_count, Sprache, Text_ID):

    min_count = int(min_count)
    NS = {'tei': 'http://www.tei-c.org/ns/1.0'}
    ROOT_NODE = ET.parse(xml_file).getroot()

    mode = get_mode(Typ)
    REFERENZ_LISTE = lade_referenz_liste_aus_xsd("kf/vmf_d1.xsd")

    textid_to_typ = {}
    for corp in ROOT_NODE.findall(".//tei:teiCorpus", NS):
        if KORPUS in corp.attrib.get("n", ""):
            for ganze in corp.findall(".//tei:TEI", NS):
                language = ganze.find(
                    ".//tei:teiHeader//tei:langUsage/tei:language", NS)
                # if language is not None and (not Sprache or language.attrib.get('ident') == Sprache):
                if not (language is not None and (not Sprache or language.attrib.get('ident') == Sprache)):
                    continue

                for text in ganze.findall(".//tei:text", NS):
                    text_xmlid = text.attrib.get(
                        '{http://www.w3.org/XML/1998/namespace}id', '')
                    # if Text_ID in text_xmlid:
                    if Text_ID not in text_xmlid:
                        continue

                    tn_all = set()
                    for segm in text.findall(".//tei:seg", NS):
                        tn = segm.attrib.get(
                            '{www.dglab.uni-jena.de/vmf/a}ana', '')
                        tn_list = [x.strip() for x in tn.replace(
                            ";", ",").split(",") if x.strip()]

                        # --- Nur Werte behalten, die mit 'a' beginnen ---
                        tn_list = [
                            x for x in tn_list if x.startswith('a')]

                        tn_all.update(tn_list)

                    # --- Prüfbedingungen ---
                    if isinstance(Typ, str):
                        # Nur ein einziger Typ erlaubt (keine Kombinationen)
                        ok = (tn_all == {Typ})
                    else:
                        ok_and = True
                        ok_or = True
                        ok_not = True

                        if "AND" in Typ:
                            ok_and = all(
                                t in tn_all for t in Typ["AND"])
                        if "OR" in Typ:
                            ok_or = any(t in tn_all for t in Typ["OR"])
                        if "NOT" in Typ:
                            ok_not = all(
                                t not in tn_all for t in Typ["NOT"])

                        # Kombination nach MODE
                        if "AND" in Typ and "OR" in Typ:
                            if mode == "OR":
                                ok = (ok_and or ok_or) and ok_not
                            else:  # MODE = "AND" (Standard)
                                ok = (ok_and and ok_or) and ok_not
                        elif "AND" in Typ:
                            ok = ok_and and ok_not
                        elif "OR" in Typ:
                            ok = ok_or and ok_not
                        else:
                            ok = ok_not

                    if ok:
                        textid_to_typ[text_xmlid] = True

    # --- Ergebnis als Python-Liste speichern ---
    text_ids = sorted(textid_to_typ.keys())

    # Speichern der Märchendaten für jedes `text_id`
    maerchen_daten = {ch: "" for ch in text_ids}

    # --- 4. CSV-Dateien erzeugen ---
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)

    for text_id in text_ids:
        for ganze in ROOT_NODE.findall(".//{http://www.tei-c.org/ns/1.0}text"):
            if ganze.attrib.get('{http://www.w3.org/XML/1998/namespace}id') == text_id:
                for body in ganze.findall(".//{http://www.tei-c.org/ns/1.0}body"):
                    for absatz in body.findall(".//{http://www.tei-c.org/ns/1.0}p"):
                        for phrase in absatz.findall(".//{http://www.tei-c.org/ns/1.0}seg"):
                            try:
                                labela = phrase.attrib['{www.dglab.uni-jena.de/vmf/a}ana']
                                labelb1 = phrase.attrib.get(
                                    '{www.dglab.uni-jena.de/vmf/b1}ana', 'N')
                                labelb2 = phrase.attrib.get(
                                    '{www.dglab.uni-jena.de/vmf/b2}ana', 'N')
                                labelb3 = phrase.attrib.get(
                                    '{www.dglab.uni-jena.de/vmf/b3}ana', 'N')
                                labelb4 = phrase.attrib.get(
                                    '{www.dglab.uni-jena.de/vmf/b4}ana', 'N')
                                labelb5 = phrase.attrib.get(
                                    '{www.dglab.uni-jena.de/vmf/b5}ana', 'N')
                                labelc1 = phrase.attrib.get(
                                    '{www.dglab.uni-jena.de/vmf/c1}ana', 'N')
                                labelc2 = phrase.attrib.get(
                                    '{www.dglab.uni-jena.de/vmf/c2}ana', 'N')
                                labelc3 = phrase.attrib.get(
                                    '{www.dglab.uni-jena.de/vmf/c3}ana', 'N')
                                labelc4 = phrase.attrib.get(
                                    '{www.dglab.uni-jena.de/vmf/c4}ana', 'N')
                                labelc5 = phrase.attrib.get(
                                    '{www.dglab.uni-jena.de/vmf/c5}ana', 'N')
                                labeld1 = phrase.attrib.get(
                                    '{www.dglab.uni-jena.de/vmf/d1}ana', 'N')
                                labeld2 = phrase.attrib.get(
                                    '{www.dglab.uni-jena.de/vmf/d2}ana', 'N')
                                labeld3 = phrase.attrib.get(
                                    '{www.dglab.uni-jena.de/vmf/d3}ana', 'N')
                                labeld4 = phrase.attrib.get(
                                    '{www.dglab.uni-jena.de/vmf/d4}ana', 'N')
                                labeld5 = phrase.attrib.get(
                                    '{www.dglab.uni-jena.de/vmf/d5}ana', 'N')
                                quelle = ganze.attrib['{http://www.w3.org/XML/1998/namespace}id']
                                inhalt = (phrase.text.lower().strip()
                                          .replace('|', '').replace(':', '').replace("ä", "ae")
                                          .replace("ü", "ue").replace("ö", "oe").replace("ß", "ss")
                                          .replace(",", "").replace("\n", " ").replace("'", "")
                                          .replace("…", "").replace('"', "").replace("*", "")
                                          .replace("(", "").replace(")", "").replace("-", "")
                                          .replace("]", "").replace("[", "").replace(".", "")
                                          .replace("?", "").replace("!", "").replace("„", "")
                                          .replace("+", "").replace("=", "").replace("_", "")
                                          .replace("­", "").replace('“', "").replace('”', "")
                                          .replace(";", "").replace('~', "").replace('`', "")
                                          .replace("«", "").replace("»", ""))
                                dana = ""
                                dana += (labeld1+'_'+labeld2+'_'+labeld3 +
                                         '_'+labeld4+'_'+labeld5).replace('_N', '')
                                try:
                                    labeld = sortiere_dana(
                                        dana, REFERENZ_LISTE)
                                except ValueError:
                                    labeld = dana
                                if labela.startswith('a'):
                                    maerchen_daten[text_id] += f"{quelle},{labela},{labelb1},{labelc1},{labelb2},{labelc2},{
                                        labelb3},{labelc3},{labelb4},{labelc4},{labelb5},{labelc5},{labeld},{inhalt},0\n"
                            except KeyError:
                                continue

        # CSV-Datei speichern
        csv_file = os.path.join(OUTPUT_FOLDER, f"text_{text_id}.csv")
        with open(csv_file, 'w', encoding='utf-8') as f:
            f.write('quelle,labela,labelb1,labelc1,labelb2,labelc2,labelb3,labelc3,labelb4,labelc4,labelb5,labelc5,labeld,inhalt,index_binar\n')
            f.write(maerchen_daten[text_id])

    # ------------------ Vorbereitung ------------------

    unique_values_per_ch = {}
    result_data_per_ch = {}
    gesamt_ergebnisse = {}

    # Ordnerpfade
    csv_folder = os.path.join("GF", "processed")  # Hier liegen die CSV-Dateien
    # Hier sollen die TXT-Dateien hin
    output_folder = "GF/processed"
    os.makedirs(output_folder, exist_ok=True)

    # ------------------ Verarbeitung jeder CSV ------------------
    for ch in text_ids:
        csv_file = os.path.join(csv_folder, f"text_{ch}.csv")
        if not os.path.exists(csv_file):
            print(f"CSV-Datei {csv_file} existiert nicht, wird übersprungen.")
            unique_values_per_ch[ch] = set()
            result_data_per_ch[ch] = []
            gesamt_ergebnisse[ch] = []
            continue

        # CSV einlesen
        df = pd.read_csv(csv_file, encoding='utf-8')

        # Index-Strings erstellen
        abcd_data = []
        for _, row in df.iterrows():
            labela = row['labela']
            labeld = row['labeld']
            for i in range(1, 6):
                labelb = row[f'labelb{i}']
                labelc = row[f'labelc{i}']
                abcd_data.append(f"{labela}:{labelb}:{labelc}:{labeld}")
                # abcd_data.append(f"{labela}:{labelb}:{labelc}:") #Alternativ: die vorherige Zeile kommentieren und diese aktivieren

        # Filterung der Daten (':N:' wird entfernt)
        filtered_data = [line for line in abcd_data if ':N:' not in line]

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
        unique_values_per_ch[ch] = unique_values
        result_data_per_ch[ch] = filtered_data
        gesamt_ergebnisse[ch] = filtered_data

        # XSD-Datei einlesen und Enum-Werte mit Leerzeichen extrahieren
        fk_tree = ET.parse('kf/vmf_a.xsd').getroot()
        enum_elements = fk_tree.findall(
            ".//{http://www.w3.org/2001/XMLSchema}enumeration")
        enum_values_with_spaces = {
            enum.attrib['value'] for enum in enum_elements if ' ' in enum.attrib['value']}

        # ------------------ GF-Dateien speichern ------------------
        output_filename = os.path.join(output_folder, f"{ch}.txt")
        with open(output_filename, "w", encoding="utf-8") as file:
            # Optional: Matching-Werte aus XSD berücksichtigen
            matching_values = [
                value for value in enum_values_with_spaces
                if any(value.split(' ')[0] == uval for uval in unique_values)
            ]
            for result in filtered_data:
                file.write(f"{result}\n")

    # ------------------ CSV-Dateien löschen (optional) ------------------
    for ch in text_ids:
        csv_file = os.path.join(csv_folder, f"text_{ch}.csv")
        if os.path.exists(csv_file):
            try:
                os.remove(csv_file)
            except Exception as e:
                print(f"Fehler beim Löschen von {csv_file}: {e}")

# --- Parameter ---
    ordner = output_folder
    ziel_datei = "eindeutige_zeilen.txt"

    # Counter für Zeilen
    zeilen_counter = Counter()

    # Prüfen, ob Ordner existiert
    if not os.path.exists(ordner):
        raise FileNotFoundError(f"Ordner '{ordner}' existiert nicht!")

    for dateiname in os.listdir(ordner):
        if dateiname.endswith(".txt"):
            dateipfad = os.path.join(ordner, dateiname)
            with open(dateipfad, "r", encoding="utf-8") as f:
                for zeile in f:
                    z = zeile.strip()
                    if z:
                        zeilen_counter[z] += 1

    # Zeilen, die mindestens min_count-mal vorkommen
    eindeutige_zeilen = {zeile for zeile,
                         count in zeilen_counter.items() if count >= min_count}

    # Ergebnis in Datei speichern
    with open(ziel_datei, "w", encoding="utf-8") as f:
        for zeile in sorted(eindeutige_zeilen):
            f.write(zeile + "\n")

    print(f"Fertig! {len(eindeutige_zeilen)
                     } eindeutige Zeilen gespeichert in {ziel_datei}")

    return gesamt_ergebnisse, eindeutige_zeilen, text_ids


def make_folder_name(chisch_liste):
    if isinstance(chisch_liste, list):
        return "_".join(chisch_liste)
    elif isinstance(chisch_liste, str):
        return chisch_liste
    else:
        raise TypeError("chisch muss String oder Liste sein.")

# --- Schritt 1: Eindeutige Zeilen erstellen ---


def create_unique_lines(folder, ziel_datei, min_count):
    if not os.path.exists(folder):
        print(f"Fehler: Ordner '{folder}' existiert nicht!")
        return set()

    files = [f for f in os.listdir(folder) if f.endswith(".txt")]
    if not files:
        print(f"Fehler: Keine .txt-Dateien im Ordner '{folder}' gefunden!")
        return set()

    zeilen_counter = Counter()
    for dateiname in files:
        dateipfad = os.path.join(folder, dateiname)
        with open(dateipfad, "r", encoding="utf-8") as f:
            for zeile in f:
                z = zeile.strip()
                if z:
                    zeilen_counter[z] += 1

    eindeutige_zeilen = {zeile for zeile,
                         count in zeilen_counter.items() if count >= min_count}

    with open(ziel_datei, "w", encoding="utf-8") as f:
        for zeile in sorted(eindeutige_zeilen):
            f.write(zeile + "\n")

    print(f"{len(eindeutige_zeilen)} eindeutige Zeilen gespeichert in {ziel_datei}")
    return eindeutige_zeilen

# --- Basisdatei einlesen ---


def read_file(filename):
    with open(filename, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

# --- Paarweise Stimmen sammeln ---


def collect_pair_votes(base_lines, comparison_files):
    votes = defaultdict(int)
    base_set = set(base_lines)
    for file in comparison_files:
        lines = read_file(file)
        lines = [l for l in lines if l in base_set]
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


def sort_base(base_file, comparison_folder):
    base_lines = read_file(base_file)
    comparison_files = [
        os.path.join(comparison_folder, f)
        for f in sorted(os.listdir(comparison_folder))
        if f.endswith(".txt")
    ]
    if not comparison_files:
        print("Keine Vergleichsdateien gefunden.")
        return base_lines
    votes = collect_pair_votes(base_lines, comparison_files)
    graph, indegree, used_nodes = build_majority_graph(base_lines, votes)
    sorted_lines = topo_sort(graph, indegree, used_nodes)

    # Nicht verwendete Zeilen hinten anhängen + markieren
    for line in base_lines:
        if line not in sorted_lines:
            marked_line = f"*{line}"
            sorted_lines.append(marked_line)
    return sorted_lines

# --- Hauptprogramm ---


def grundform(data):

    min_count = int(data["min_count"])
    _, eindeutige_zeilen, chisch = eindeutige_zeilen_erstellen(**data)

    base_file = "eindeutige_zeilen.txt"  # Basisdatei
    folder_name = OUTPUT_FOLDER  # Ordner aus chisch-Liste, nicht Typ
    ziel_datei = base_file

    # Eindeutige Zeilen erstellen
    create_unique_lines(folder_name, ziel_datei, min_count)

    # Sortierung nach Mehrheitsregeln
    sorted_lines = sort_base(base_file, folder_name)

    zeilen = []
    for i in range(0, len(chisch), 3):
        zeilen.append("\t".join(f"'{w}'" for w in chisch[i:i+3]))

#     output_text = f"""Typ(en) = {data["Typ"]}
# Häufigkeit = {min_count}
# Text-IDs:\n"  {"\n".join(zeilen)}
# ---------------------
#
# """
    output_text = f"Typ(en) = {data['Typ']}"
    output_text += "\n"
    output_text += f"Häufigkeit = {min_count}"
    output_text += "\n"
    output_text += "Text-IDs:"
    output_text += "\n"
    output_text += '\n'.join(zeilen)
    output_text += "\n---------------------\n\n"

    for line in sorted_lines:
        if line.startswith("*"):
            output_text += f"<b>{line}</b>\n"
        else:
            output_text += f"{line}\n"

    return output_text


if __name__ == "__main__":
    config = {
        "xml_file": 'xml_sources/ava_deu.xml',
        "korpus": "",
        "Typ": {"AND": ["a460A"]},
        "min_count": '1',
        "Sprache": "",
        "Text_ID": ""
    }

    gf = grundform(config)
    print(gf)
