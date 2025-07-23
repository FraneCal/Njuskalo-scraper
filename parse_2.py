import os
import json
from bs4 import BeautifulSoup

input_dir = "backend/website"
output_dir = "backend/json"
os.makedirs(output_dir, exist_ok=True)

for filename in os.listdir(input_dir):
    if not filename.endswith(".html"):
        continue

    filepath = os.path.join(input_dir, filename)
    with open(filepath, "r", encoding="utf-8") as f:
        html = f.read()

    soup = BeautifulSoup(html, "html.parser")

    # Naslov
    title_tag = soup.find("title")
    naslov = title_tag.get_text(strip=True) if title_tag else None

    # Cijena
    price_tag = soup.select_one("dl.ClassifiedDetailSummary-priceRow dd.ClassifiedDetailSummary-priceDomestic")
    cijena = price_tag.get_text(strip=True) if price_tag else None

    # Osnovni podaci
    podaci = {
        "datoteka": filename,
        "naslov": naslov,
        "cijena": cijena
    }

    info_section = soup.select_one("div.ClassifiedDetailBasicDetails dl.ClassifiedDetailBasicDetails-list")
    if info_section:
        dt_tags = info_section.find_all("dt")
        dd_tags = info_section.find_all("dd")

        for dt, dd in zip(dt_tags, dd_tags):
            key_span = dt.find("span", class_="ClassifiedDetailBasicDetails-textWrapContainer")
            val_span = dd.find("span", class_="ClassifiedDetailBasicDetails-textWrapContainer")
            kljuc = key_span.get_text(strip=True) if key_span else None
            vrijednost = val_span.get_text(strip=True) if val_span else None
            if kljuc and vrijednost:
                podaci[kljuc] = vrijednost

    # Opis
    desc_tag = soup.find("div", class_="ClassifiedDetailDescription-text")
    opis = desc_tag.get_text(" ", strip=True).replace("\n", " ") if desc_tag else None
    podaci["opis"] = opis

    # Dodatne informacije
    dodatne_sekcije = soup.select("section.ClassifiedDetailPropertyGroups-group")
    for sekcija in dodatne_sekcije:
        naslov_grupe = sekcija.find("h3", class_="ClassifiedDetailPropertyGroups-groupTitle")
        if not naslov_grupe:
            continue
        ime_grupe = naslov_grupe.get_text(strip=True)

        stavke = []
        elementi = sekcija.select("li.ClassifiedDetailPropertyGroups-groupListItem")
        for li in elementi:
            tekst = li.get_text(strip=True)
            if tekst:
                stavke.append(tekst)

        if stavke:
            podaci[ime_grupe] = stavke

    # Podaci o agenciji
    owner_section = soup.select_one("div.ClassifiedDetailOwnerDetails")
    if owner_section:
        agencija_tag = owner_section.select_one("h2.ClassifiedDetailOwnerDetails-title a")
        if agencija_tag:
            podaci["naziv_agencije"] = agencija_tag.get_text(strip=True)

        web_tag = owner_section.select_one("a[href^='http']:not([href^='mailto'])")
        if web_tag:
            podaci["web_agencije"] = web_tag.get("href")

        email_tag = owner_section.select_one("a[href^='mailto']")
        if email_tag:
            podaci["email_agencije"] = email_tag.get_text(strip=True)

        adresa_li = owner_section.select_one("li.ClassifiedDetailOwnerDetails-contactEntry i[aria-label='Adresa']")
        if adresa_li and adresa_li.parent:
            podaci["adresa_agencije"] = adresa_li.parent.get_text(strip=True).replace("Adresa: ", "")

        telefon_prisutan = owner_section.select_one(".UserPhoneNumber-callSeller")
        podaci["telefon_dostupan"] = bool(telefon_prisutan)

    # Slike (samo one koje sadrže 'image-xlsize' u src)
    image_tags = soup.select("img.pswp__img")
    slike = [img["src"] for img in image_tags if img.get("src") and "image-xlsize" in img["src"]]
    podaci["slike"] = slike

    # Spremanje JSON-a
    json_ime = os.path.splitext(filename)[0] + ".json"
    json_putanja = os.path.join(output_dir, json_ime)

    with open(json_putanja, "w", encoding="utf-8") as jf:
        json.dump(podaci, jf, ensure_ascii=False, indent=2)

print(f"✅ Sve spremljeno u: {output_dir}")
