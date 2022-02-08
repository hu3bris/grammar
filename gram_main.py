from flask import Flask, render_template, request
import spacy
from spacy import displacy
from urllib.request import urlopen
from bs4 import BeautifulSoup

# Load German tokenizer, tagger, parser and NER
nlp = spacy.load("de_core_news_sm")

# decensions
det = [[["der", "dieser", "jeder", "jener", "mancher", "welcher"], "mnom_fgen_fdat_"],
       [["des", "dieses", "jedes", "jenes", "manches", "welches"], "mgen_ngen_"],
       [["dem", "diesem", "jedem", "jenem", "jedem", "manchem", "welchem"], "mdat_ndat_"],
       [["den", "diesen", "jeden", "jenen", "manchen", "welchen"], "makk_"],
       [["die", "diese", "jede", "jene", "manche", "welche"], "fnom_fakk_"],
       [["das", "dieses", "jedes", "jenes", "manches", "welches"], "nnom_nakk_"]]
dec_adj = ["er", "en", "em", "es", "e"]
dec_adj_ = [["e", "mnom_fnom_fakk_nnom_nakk_"], ["en", "mgen_mdat_makk_fgen_fdat_ngen_ndat_"]]

def check_for_adjectives(phrase):
    global dec_adj
    adjectives = []
    output = []
    for ix, token in enumerate(phrase):
        output.append(token.text)
        if token.pos_ == "ADJ":
            entry = [token.text]
            # separate declension -------------
            if token.text[-2:] in dec_adj:
                entry = [token.text[:-2], token.text[-2:]]
            elif token.text[-1:] in dec_adj:
                entry = [token.text[:-1], token.text[-1:]]
            else:
                entry = [token.text, "xx"]

            # Adjektive in Liste + Artikel(links) und Nomen(rechts)
            if phrase[ix - 1].pos_ == "DET":
                entry.append(str("pre_" + phrase[ix - 1].text))
            else:
                entry.append("pre_none")
            if phrase[ix + 1].pos_ == "NOUN":
                entry.append(str("pos_" + phrase[ix + 1].text))
            else:
                entry.append("pos_none")

            # Funktion zum Abgleich aufrufen
            comp = compare(entry)[0]
            # Info über Adjektive sammeln (=adjectives)
            entry.append(comp)
            adjectives.append(entry)
            # Text mit Korrektur sammeln (=output)
            comp = "(" + comp + ")"
            output.append(comp)

    return adjectives, output


def get_gender_noun(noun):
    gender = noun
    html_path = "https://www.verbformen.de/?w=" + noun
    try:
        with urlopen(html_path) as quelldatei:
            html_text = quelldatei.read().decode('utf-8', 'ignore')
            soup = BeautifulSoup(html_text, 'html.parser')
    except:
        gender += " --> fail1"
    try:
        gender = soup.find('p', {'class': 'rInf'})
        gender = gender.text
        if "Maskulin" in gender:
            gender = "mnom_mgen_mdat_makk_"
        elif "Feminin" in gender:
            gender = "fnom_fgen_fdat_fakk_"
        elif "Neutral" in gender:
            gender = "nnom_ngen_ndat_nakk_"
        else:
            gender += " --> fail3"
    except AttributeError:
        gender += " --> fail2"

    # Problem mit Umlauten !!!
    return gender


def get_pos_det(article):
    global det
    # "article[4:]" um "det_" zu entfernen
    checked = "unknown det -->" + article[4:]
    # für jeden Eintrag in der globalen Liste "det"
    for declension in det:
        # wenn der Artikel vor dem Adjektiv in der globalen Liste enthalten ist, gib mir sein POS
        if article[4:].casefold() in declension[0]:
            checked = declension[1]

    return checked


def compare(adjectives):
    check = []
    global dec_adj_

    # Endungen des Adjektivs auf POS überprüfen
    y = "dec_of_adj_not_found"
    for declension in dec_adj_:
        if adjectives[1] == declension[0]:
            y = declension[1]
    check.append(y)

    # Endungen des Artikels auf POS überprüfen (nur bestimmter Artikel!!)
    if adjectives[2] != "pre_none":
        x = get_pos_det(adjectives[2])
        check.append(x)
    else:
        check.append("pre_none")

    # GENUS der Nomen suchen (Problem mit Umlauten!!)
    if adjectives[3] != "pos_none":
        x = get_gender_noun(adjectives[3])
        check.append(x)
    else:
        check.append("pos_none")

    # wenn es POS für das Adjektiv gibt
    if check[0] != "dec_of_adj_not_found":

        # für jede POS des Adjektivs
        for dec_0 in check[0].split('_'):

            # wenn es auch POS für das Nomen gibt
            if check[2] != "pos_none":

                # wenn POS des Adjektivs nicht in POS des Nomens, POS des Adjektivs entfernen
                if dec_0 not in check[2]:
                    check[0] = check[0].replace(dec_0 + "_", "")

            # wenn es auch POS für den Artikel gibt
            if check[1] != "pre_none":

                # wenn POS des Adjektivs nicht in POS des Artikels, POS des Adjektivs entfernen
                if dec_0 not in check[1]:
                    check[0] = check[0].replace(dec_0 + "_", "")

        # wenn keine POS des Adjektivs übrig bleibt
        if check[0] == "":
            check[0] = "fehler"

    return check


app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    name = None
    temp = None
    text_ = ("Jeder freche Junge ist in der Garage. Jede junge Frau läuft ins Geschäft. Junges Ding schläft.")

    if request.method == 'POST' and 'name' in request.form:
        name = request.form['name']
        temp = name
        doc = nlp(name)
        name = check_for_adjectives(doc)
    return render_template('index.html', name=name, temp=temp)

if __name__ == '__main__':
    app.run(debug=True)

