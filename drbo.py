#!/usr/bin/env python3
import os
from itertools import groupby

import requests
from bs4 import BeautifulSoup

TEMPLATES_DIR = "templates"
OUTPUT_DIR = "output"

BILINGUAL_URL = "http://www.drbo.org/drl/chapter/47001.htm"
DR_URL = "http://www.drbo.org/chapter/47001.htm"

BOOKNAME_SELECTOR = "td.bookname"
CHAPNAME_SELECTOR = "td.chapname"
PARAGRAPH_SELECTOR = "td.textarea > p"

# request the webpage
r = requests.get(BILINGUAL_URL)
soup = BeautifulSoup(r.content, "lxml")
bookname = soup.select(BOOKNAME_SELECTOR)[0].text
chapname = soup.select(CHAPNAME_SELECTOR)[0].text
paragraphs = soup.select(PARAGRAPH_SELECTOR)

# read in LaTeX templates
templates = {}
for filename in os.listdir(TEMPLATES_DIR):
    if filename.endswith(".tex"):
        with open(f"./{TEMPLATES_DIR}/{filename}", "r") as f:
            templates[filename] = f.read()

# convert the paragraphs to LaTeX
latex_lines = []
paragraph_data = []
for p in paragraphs:
    lat_p = p.font
    if lat_p:
        latin_text = lat_p.text
        p.font.decompose()
        paragraph_data.append({
            "english": p.text,
            "latin": latin_text,
        })
    else:
        paragraph_data.append({
            "english": p.text,
            "latin": None,
        })


def is_bilingual(paragraph):
    return(paragraph["latin"] is not None)


# group paragraphd into seequences of bilingual or monolingual paragraphs
groups = []
for k, g in groupby(paragraph_data, is_bilingual):
    groups.append({"bilingual": k, "paragraphs": list(g)})

for group in groups:
    if group["bilingual"]:
        # set up parallel texts
        latex_lines.append(templates["start-parallel.tex"])
        # separate the two languages into lists
        latin = templates["between-paragraphs.tex"].join(p["latin"] for p in group["paragraphs"])
        english = templates["between-paragraphs.tex"].join(p["english"] for p in group["paragraphs"])
        latex_lines.append(latin)
        latex_lines.append(templates["between-languages.tex"])
        latex_lines.append(english)
        latex_lines.append(templates["end-parallel.tex"])
    else:
        # monolingual, just add all of these on as normal text
        latex_lines += [p["english"] for p in group["paragraphs"]]

document = [templates["preamble.tex"]] + latex_lines + [templates["end.tex"]]
document = "\n".join(document)
if not os.path.exists(OUTPUT_DIR):
    os.makedirs(OUTPUT_DIR)

with open(f"{OUTPUT_DIR}/drbo.tex", "w") as f:
    f.write(document)

# lualatex --shell-escape -output-dir=output output/drbo.tex
