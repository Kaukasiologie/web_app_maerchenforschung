import json
from multiprocessing import Value
from hilfsfunktoinen import sonderzeichen_entfernen, sonderzeichen_entfernen_old

strippable_text_1 = r"""tagen spätabends kam beim wirtshaus an, zwei brüder sitzen geblieben waren. »jetzt«, sagte
selbst, »kannst wohl gütlich tun, nachdem schönes stück arbeit vollbracht hast. stieg deshalb ab ging brüdern hinein.
abgang geldes allmählich stiller geworden saßen ganz trübsinnig [winkel]. eintreten sahen, sprangen freude baten ihn,
erzählen, ergangen war. !erzählte ganze geschichte zeigte flasche heilwasser. tag hause könnten, kaufte pferde los legte
wohlgemut argwohn schlafen."""

strippable_text = r"""spätabends  AN, zwei |brüder sitzen geblieben waren! »jetzt«,
(allmählich) ?stiller*; ~saßen ganz trübsinnig [winkel]. wohlgemut argwohn schlafen."""

stripped_text = r"""spaetabends  an zwei brueder sitzen geblieben waren jetzt allmaehlich stiller sassen ganz truebsinnig winkel wohlgemut argwohn schlafen"""


def deutsche_sonderzeichen():
    config_file_name = "configs/sonderzeichen_config.json"
    with open(config_file_name, "r") as config_file:
        config = json.load(config_file)
    for el in config:
        if el["language"] == "german":
            german_config = el
            return german_config["sonderzeichen"]
        else:
            raise ValueError("Attempting to read a config that does not exist")


def test_compare_handwritten_stripped_text():

    sonderzeichen = deutsche_sonderzeichen()
    new_stripped = sonderzeichen_entfernen(strippable_text, sonderzeichen)

    assert new_stripped == stripped_text


def test_old_new_comp_1():
    old_stripped = sonderzeichen_entfernen_old(strippable_text_1)

    sonderzeichen = deutsche_sonderzeichen()
    new_stripped = sonderzeichen_entfernen(strippable_text_1, sonderzeichen)

    assert old_stripped == new_stripped


def test_none():

    new_stripped = sonderzeichen_entfernen(strippable_text, None)

    assert strippable_text.lower().strip() == new_stripped
