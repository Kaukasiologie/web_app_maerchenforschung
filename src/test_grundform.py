import json
from old_grundform import eindeutige_zeilen_erstellen as eindeutige_zeilen_erstellen_old
from old_grundform import grundform as grundform_old
from grundform import eindeutige_zeilen_erstellen
from grundform import grundform

import shutil
import os


def cleanup():
    # pass
    if os.path.isdir('GF'):
        shutil.rmtree("GF")


cleanup()

TYP = {"AND": ["a460A"]}
TYP_STRING = '{"AND": ["a460A"]}'
SPRACHE = ""
TEXT_ID = ""


def test_saninty_check():

    xml_file = 'xml_sources/ava_deu.xml'

    ava_deu_golden = """a460A:h:STERBEN:rEHDem_rJHDem
a460A:F:TRAUM:rEHDem_rJHDem
a460A:F:Jenseitswanderung_unternehmen:rEHDem_rJHDem
a460A:F:Folge_von_Kriminalität_deuten:rEHDem_rEVMeU
a460A:F:Lösungsweg_für_leidendes_Tier_deuten:rEHDem_fEVMeu
a460A:F:Folge_von_Bigotterie_deuten:rEHDem_fEVMew
a460A:F:Lösungsweg_für_sonstiges_Leid_deuten:rEHDem_rEVMeu
a460A:H:Begegnung:rEHDem_rEHFeu
a460A:H:Vermittlung:rEHDem_rEHFeu
a460A:H:Information_aus_zweiter_Hand:rEHDem_rEHFeu
a460A:h:Lösungsweg_für_leidendes_Tier_deuten:rEHDem_rEHFeu
a460A:H:Information_aus_zweiter_Hand:rEHDem_rEHFeu_+
a460A:h:Folge_von_Bigotterie_deuten:rEHDem_rEHFeu
a460A:H:Information_aus_zweiter_Hand:rEHDem_rEHFeu_+_+
a460A:h:Lösungsweg_für_sonstiges_Leid_deuten:rEHDem_rEHFeu
a460A:H:Information_aus_zweiter_Hand:rEHDem_rEHFeu_+_+_+
a460A:h:Lösungsweg_für_sonstiges_Leid_deuten:rEHDem_rEHFeu_+"""

    _, res, text_ids = eindeutige_zeilen_erstellen_old(xml_file,
                                                       korpus="",
                                                       Typ=TYP,
                                                       min_count=1,
                                                       Sprache=SPRACHE,
                                                       Text_ID=TEXT_ID)

    assert res == set(ava_deu_golden.split('\n'))
    assert text_ids == ['zyx_cc_ava_deu_213']


def test_creation1():

    xml_file = 'ava_deu.xml'

    ava_deu_golden = """a460A:h:STERBEN:rEHDem_rJHDem
a460A:F:TRAUM:rEHDem_rJHDem
a460A:F:Jenseitswanderung_unternehmen:rEHDem_rJHDem
a460A:F:Folge_von_Kriminalität_deuten:rEHDem_rEVMeU
a460A:F:Lösungsweg_für_leidendes_Tier_deuten:rEHDem_fEVMeu
a460A:F:Folge_von_Bigotterie_deuten:rEHDem_fEVMew
a460A:F:Lösungsweg_für_sonstiges_Leid_deuten:rEHDem_rEVMeu
a460A:H:Begegnung:rEHDem_rEHFeu
a460A:H:Vermittlung:rEHDem_rEHFeu
a460A:H:Information_aus_zweiter_Hand:rEHDem_rEHFeu
a460A:h:Lösungsweg_für_leidendes_Tier_deuten:rEHDem_rEHFeu
a460A:H:Information_aus_zweiter_Hand:rEHDem_rEHFeu_+
a460A:h:Folge_von_Bigotterie_deuten:rEHDem_rEHFeu
a460A:H:Information_aus_zweiter_Hand:rEHDem_rEHFeu_+_+
a460A:h:Lösungsweg_für_sonstiges_Leid_deuten:rEHDem_rEHFeu
a460A:H:Information_aus_zweiter_Hand:rEHDem_rEHFeu_+_+_+
a460A:h:Lösungsweg_für_sonstiges_Leid_deuten:rEHDem_rEHFeu_+"""

    _, res, text_ids = eindeutige_zeilen_erstellen(xml_file,
                                                   typ_input=TYP_STRING,
                                                   min_count=1)
    assert res == set(ava_deu_golden.split('\n'))
    assert text_ids == ['zyx_cc_ava_deu_213']
    cleanup()


def test_creation2():

    xml_file = 'ava_deu.xml'
    xml_file_old = f'xml_sources/{xml_file}'

    new_res = eindeutige_zeilen_erstellen(xml_file,
                                          typ_input=TYP_STRING,
                                          min_count=1)

    old_res = eindeutige_zeilen_erstellen_old(xml_file_old,
                                              korpus="",
                                              Typ=TYP,
                                              min_count=1,
                                              Sprache=SPRACHE,
                                              Text_ID=TEXT_ID)

    assert new_res == old_res
    cleanup()


def test_creation3():

    xml_file = 'ava_deu.xml'
    xml_file_old = f'xml_sources/{xml_file}'

    all_res_new, _, _ = eindeutige_zeilen_erstellen(xml_file,
                                                    typ_input=TYP_STRING,
                                                    min_count=1,)

    all_res_old, _, _ = eindeutige_zeilen_erstellen_old(xml_file_old,
                                                        korpus="",
                                                        Typ=TYP,
                                                        min_count=1,
                                                        Sprache=SPRACHE,
                                                        Text_ID=TEXT_ID)

    sorted_new = dict(sorted(all_res_new.items()))
    sorted_old = dict(sorted(all_res_old.items()))

    assert sorted_new == sorted_old
    cleanup()


def test_retro_grundform1():
    config = {
        "xml_database_name": 'ava_deu.xml',
        "typ_input": '{"AND": ["a300"]}',
        "min_count": '1',
    }
    config_old = {
        "xml_file": f'xml_sources/{config["xml_database_name"]}',
        "Typ": json.loads(config["typ_input"]),
        "min_count": config["min_count"],
        "korpus": "",
        "Sprache": SPRACHE,
        "Text_ID": TEXT_ID
    }
    gf = grundform(config)
    gf_old = grundform_old(config_old)

    assert gf == gf_old


def test_retro_grundform2():
    config = {
        "xml_database_name": 'dgstn.xml',
        "typ_input": '{"AND": ["a300"]}',
        "min_count": '2'
    }
    config_old = {
        "xml_file": f'xml_sources/{config["xml_database_name"]}',
        "Typ": json.loads(config["typ_input"]),
        "min_count": config["min_count"],
        "korpus": "",
        "Sprache": SPRACHE,
        "Text_ID": TEXT_ID
    }

    gf = grundform(config)
    gf_old = grundform_old(config_old)

    assert gf == gf_old
    cleanup()


def test_retro_grundform3():

    config = {
        "xml_database_name": 'dgstn.xml',
        "typ_input": '{"AND": ["a563","a425A"], "OR": ["a300"], "NOT": ["a700"], "MODE": "OR"}',
        "min_count": '2'
    }

    config_old = {
        "xml_file": f'xml_sources/{config["xml_database_name"]}',
        "Typ": json.loads(config["typ_input"]),
        "min_count": config["min_count"],
        "korpus": "",
        "Sprache": SPRACHE,
        "Text_ID": TEXT_ID
    }

    gf = grundform(config)
    gf_old = grundform_old(config_old)

    assert gf == gf_old
    cleanup()
