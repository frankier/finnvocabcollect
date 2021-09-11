from lxml import etree


NSS_XML_PATH = "kotus-sanalista_v1/kotus-sanalista_v1.xml"
COMPOUND_LIST = "compound_list.txt"
BAD_CATEGORIES = "badcatlist.txt"
DEFAULT_POS_FILTER = ["V", "N", "A", "Adv", "Adp"]
ALL_POS = [*DEFAULT_POS_FILTER, "Pron", "Num", "C", "Interj"]
PRODUCTIVE_DERIVATIONS = [
    # -ly
    ("Adv", "sti"),
    # -less
    ("A", "ton"),
    ("A", "tön"),
    # -ness
    ("N", "yys"),
    ("N", "uus"),

    #ja
    #inen
    #lainen
]


def read_compound_list():
    res = set()
    with open(COMPOUND_LIST) as compounds:
        for line in compounds:
            word = line.strip()
            if word:
                res.add(word.lower())
    return res


def read_bad_list():
    res = set()
    with open(BAD_CATEGORIES) as badcatlist:
        for line in badcatlist:
            word = line.strip()
            if word:
                res.add(word)
    return res


def read_nss(no_compound=False):
    """
    Reads Kotimaisten Kielten Keskuksen Nykysuomen Sanalista from
    https://kaino.kotus.fi/sanat/nykysuomi/
    """
    res = set()
    if no_compound:
        compound_list = read_compound_list()
    for elem in etree.parse(NSS_XML_PATH).xpath("//s"):
        if no_compound:
            if "-" in elem.text or " " in elem.text:
                continue
            if elem.text in compound_list:
                continue
            tns = elem.xpath("..//tn")
            if not tns:
                continue
            if tns[0].text in ("50", "51"):
                continue
        res.add(elem.text)
    return res
