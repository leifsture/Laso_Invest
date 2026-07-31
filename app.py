import os
import streamlit as st
import pandas as pd
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm

st.set_page_config(page_title="Laso Invest AB – Fakturaunderlag", page_icon="💼", layout="wide")

DATA_FILE = "laso_invest_data.csv"
ARTICLE_FILE = "laso_invest_artiklar.csv"

DATA_COLUMNS = [
    "ID", "Datum", "Artikelnr", "Artikel", "Kategori",
    "Kund_OrgNr", "Kund_Namn", "Kund_Adress", "Kund_Postnr", "Kund_Ort",
    "Faktura_Namn", "Faktura_Adress", "Faktura_Postnr", "Faktura_Ort",
    "Beskrivning", "Timmar", "Timpris", "Totalt"
]
ARTICLE_COLUMNS = ["Kategori", "Artikelnr", "Artikel", "ArtPris"]

DEFAULT_ARTICLES = [
    # Grävmaskin Volvo 50D
    {"Kategori": "Grävmaskin Volvo 50D", "Artikelnr": "25100", "Artikel": "Volvo 50 D", "ArtPris": "500.00"},
    {"Kategori": "Grävmaskin Volvo 50D", "Artikelnr": "25101", "Artikel": "Förare grävmaskin", "ArtPris": "400.00"},
    {"Kategori": "Grävmaskin Volvo 50D", "Artikelnr": "25102", "Artikel": "Rotor encon, grip, centralsmörjning", "ArtPris": "160.00"},
    {"Kategori": "Grävmaskin Volvo 50D", "Artikelnr": "25103", "Artikel": "Grävskopa 60 cm", "ArtPris": "20.00"},
    {"Kategori": "Grävmaskin Volvo 50D", "Artikelnr": "25104", "Artikel": "Planeringsskopa 110 cm", "ArtPris": "30.00"},
    {"Kategori": "Grävmaskin Volvo 50D", "Artikelnr": "25105", "Artikel": "Smalskopa 20 cm", "ArtPris": "15.00"},
    {"Kategori": "Grävmaskin Volvo 50D", "Artikelnr": "25106", "Artikel": "Tjälkrok", "ArtPris": "15.00"},
    {"Kategori": "Grävmaskin Volvo 50D", "Artikelnr": "25107", "Artikel": "Kratta 160 cm", "ArtPris": "20.00"},
    {"Kategori": "Grävmaskin Volvo 50D", "Artikelnr": "25108", "Artikel": "Sop 160 cm", "ArtPris": "20.00"},
    {"Kategori": "Grävmaskin Volvo 50D", "Artikelnr": "25109", "Artikel": "Grip och tillsats för kunna dra på rot", "ArtPris": "40.00"},
    {"Kategori": "Grävmaskin Volvo 50D", "Artikelnr": "25110", "Artikel": "Planeringsbalk med rulle 200 cm", "ArtPris": "40.00"},
    {"Kategori": "Grävmaskin Volvo 50D", "Artikelnr": "25111", "Artikel": "Gallerskopa", "ArtPris": "30.00"},
    {"Kategori": "Grävmaskin Volvo 50D", "Artikelnr": "25112", "Artikel": "Pallgafflar", "ArtPris": "30.00"},
    {"Kategori": "Grävmaskin Volvo 50D", "Artikelnr": "25113", "Artikel": "Vägrensare, ex mellan vägräcken", "ArtPris": "25.00"},
    {"Kategori": "Grävmaskin Volvo 50D", "Artikelnr": "25114", "Artikel": "Lång skopa smal", "ArtPris": "25.00"},
    {"Kategori": "Grävmaskin Volvo 50D", "Artikelnr": "25115", "Artikel": "Buskröjare aggregat 100 cm", "ArtPris": "80.00"},
    {"Kategori": "Grävmaskin Volvo 50D", "Artikelnr": "25116", "Artikel": "Hydraulisk trädklipp 20 cm", "ArtPris": "50.00"},

    # Lundberg 6240
    {"Kategori": "Traktor Lundberg 6240", "Artikelnr": "25200", "Artikel": "Lundberg 6240 inkl förare", "ArtPris": "500.00"},
    {"Kategori": "Traktor Lundberg 6240", "Artikelnr": "25201", "Artikel": "Förare traktor", "ArtPris": "400.00"},
    {"Kategori": "Traktor Lundberg 6240", "Artikelnr": "25202", "Artikel": "Planeringsskopa 220 cm bred", "ArtPris": "30.00"},
    {"Kategori": "Traktor Lundberg 6240", "Artikelnr": "25203", "Artikel": "Pallgafflar, förlängningsgafflar", "ArtPris": "30.00"},
    {"Kategori": "Traktor Lundberg 6240", "Artikelnr": "25204", "Artikel": "Multiskopa, snö ex vingar 3,60 cm", "ArtPris": "60.00"},
    {"Kategori": "Traktor Lundberg 6240", "Artikelnr": "25205", "Artikel": "Grip på lastare", "ArtPris": "40.00"},
    {"Kategori": "Traktor Lundberg 6240", "Artikelnr": "25206", "Artikel": "Kranarm", "ArtPris": "30.00"},
    {"Kategori": "Traktor Lundberg 6240", "Artikelnr": "25207", "Artikel": "Sandspridare, Drivex, 1,5 kubik 2,5 ton", "ArtPris": "40.00"},
    {"Kategori": "Traktor Lundberg 6240", "Artikelnr": "25208", "Artikel": "Sandspridare fram skopa 800l", "ArtPris": "30.00"},
    {"Kategori": "Traktor Lundberg 6240", "Artikelnr": "25209", "Artikel": "1st Hyvelblad, isrivare 260 cm", "ArtPris": "40.00"},
    {"Kategori": "Traktor Lundberg 6240", "Artikelnr": "25210", "Artikel": "1st hyvel med hjulpar 180cm+", "ArtPris": "40.00"},
    {"Kategori": "Traktor Lundberg 6240", "Artikelnr": "25211", "Artikel": "Långskopa, bredd 80cm längd 185cm", "ArtPris": "25.00"},
    {"Kategori": "Traktor Lundberg 6240", "Artikelnr": "25212", "Artikel": "Skopa 2,00 snö, lättare material/matjord", "ArtPris": "30.00"},
    {"Kategori": "Traktor Lundberg 6240", "Artikelnr": "25213", "Artikel": "Grusfräs 2,00m", "ArtPris": "70.00"},
    {"Kategori": "Traktor Lundberg 6240", "Artikelnr": "25214", "Artikel": "Hydrauliska pallgafflar 150 längd", "ArtPris": "35.00"},
    {"Kategori": "Traktor Lundberg 6240", "Artikelnr": "25215", "Artikel": "Hydraulisk slagklippare 200cm bred", "ArtPris": "120.00"},

    # Övrigt
    {"Kategori": "Övrigt", "Artikelnr": "25300", "Artikel": "Släp kåpa, tipp", "ArtPris": "60.00"},
    {"Kategori": "Övrigt", "Artikelnr": "25301", "Artikel": "Avvägningsinstrument Laser", "ArtPris": "25.00"},
    {"Kategori": "Övrigt", "Artikelnr": "25302", "Artikel": "Instrument för Ledningskoll", "ArtPris": "25.00"},
    {"Kategori": "Övrigt", "Artikelnr": "25303", "Artikel": "Padda manuell Diesel", "ArtPris": "60.00"},
    {"Kategori": "Övrigt", "Artikelnr": "25400", "Artikel": "Biggab tippvagn Lastväxlare 7-10ton", "ArtPris": "160.00"},
    {"Kategori": "Övrigt", "Artikelnr": "25401", "Artikel": "Lastbil / Lastväxlare Entreprenad", "ArtPris": "1250.00"},
    {"Kategori": "Övrigt", "Artikelnr": "25402", "Artikel": "Etablering", "ArtPris": "900.00"},
    {"Kategori": "Övrigt", "Artikelnr": "25403", "Artikel": "Av-etablering", "ArtPris": "900.00"},
    {"Kategori": "Övrigt", "Artikelnr": "25404", "Artikel": "4-hjuling el, spel", "ArtPris": "150.00"},
    {"Kategori": "Övrigt", "Artikelnr": "25405", "Artikel": "Så, vält", "ArtPris": "30.00"},
    {"Kategori": "Övrigt", "Artikelnr": "25406", "Artikel": "Harv", "ArtPris": "25.00"},
    {"Kategori": "Övrigt", "Artikelnr": "25407", "Artikel": "Mindre tippvagn", "ArtPris": "40.00"},
    {"Kategori": "Övrigt", "Artikelnr": "25500", "Artikel": "Maskinist (Hyra av maskin)", "ArtPris": "460.00"},
    {"Kategori": "Övrigt", "Artikelnr": "25501", "Artikel": "Spadgubbe", "ArtPris": "440.00"},
    {"Kategori": "Övrigt", "Artikelnr": "25502", "Artikel": "Resor Bil (per mil)", "ArtPris": "60.00"},
    {"Kategori": "Övrigt", "Artikelnr": "25503", "Artikel": "Projektledare", "ArtPris": "550.00"},
    {"Kategori": "Övrigt", "Artikelnr": "25504", "Artikel": "Utsättning", "ArtPris": "350.00"},
    {"Kategori": "Övrigt", "Artikelnr": "25505", "Artikel": "Uppritning", "ArtPris": "550.00"},
    {"Kategori": "Övrigt", "Artikelnr": "25506", "Artikel": "Bil med verktyg", "ArtPris": "300.00"},
]

def clean_str(val):
    if val is None: return ""
    s = str(val).strip()
    return "" if s.lower() == "nan" or s == "<NA>" else s

def load_data():
    if os.path.exists(DATA_FILE):
        try:
            df = pd.read_csv(DATA_FILE, dtype=str).fillna("")
            for col in DATA_COLUMNS:
                if col not in df.columns: df[col] = ""
            return df[DATA_COLUMNS]
        except Exception: return pd.DataFrame(columns=DATA_COLUMNS)
    return pd.DataFrame(columns=DATA_COLUMNS)

def save_data(df): df.to_csv(DATA_FILE, index=False)

def default_articles():
    df = pd.DataFrame(DEFAULT_ARTICLES)
    df.to_csv(ARTICLE_FILE, index=False)
    return df

def load_articles():
    if os.path.exists(ARTICLE_FILE):
        try:
            df = pd.read_csv(ARTICLE_FILE, dtype=str).fillna("")
            for col in ARTICLE_COLUMNS:
                if col not in df.columns: df[col] = ""
            return df[ARTICLE_COLUMNS]
        except Exception: return default_articles()
    return default_articles()

def save_articles(df): df.to_csv(ARTICLE_FILE, index=False)

def generate_pdf_file(customer_name, records, filepath):
    if records is None or len(records) == 0: return False
    doc = SimpleDocTemplate(filepath, pagesize=A4, rightMargin=1.5*cm, leftMargin=1.5*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)
    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle("DocTitle", parent=styles["Heading1"], fontSize=18, textColor=colors.HexColor("#1A365D"))
    meta_style = ParagraphStyle("MetaText", parent=styles["Normal"], fontSize=9, leading=12)
    meta_bold = ParagraphStyle("MetaTextBold", parent=styles["Normal"], fontSize=9, leading=12, fontName="Helvetica-Bold")

    first_rec = records.iloc[0]
    header_data = [[
        Paragraph("<b>LASO INVEST AB</b><br/>Fakturunderlag", title_style),
        Paragraph(f"<b>Datum:</b> {date.today().strftime('%Y-%m-%d')}<br/><b>Org.nr/Pers.nr:</b> {clean_str(first_rec.get('Kund_OrgNr', ''))}", meta_style)
    ]]
    header_table = Table(header_data, colWidths=[11*cm, 7*cm])
    header_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('ALIGN', (1,0), (1,0), 'RIGHT')]))
    story.append(header_table)
    story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#1A365D"), spaceBefore=8, spaceAfter=12))

    k_namn, k_adr = clean_str(first_rec.get('Kund_Namn', '')), clean_str(first_rec.get('Kund_Adress', ''))
    k_post, k_ort = clean_str(first_rec.get('Kund_Postnr', '')), clean_str(first_rec.get('Kund_Ort', ''))
    f_namn = clean_str(first_rec.get('Faktura_Namn', '')) or k_namn
    f_adr = clean_str(first_rec.get('Faktura_Adress', '')) or k_adr
    f_post = clean_str(first_rec.get('Faktura_Postnr', '')) or k_post
    f_ort = clean_str(first_rec.get('Faktura_Ort', '')) or k_ort

    kund_info = f"<b>KUND:</b><br/>{k_namn}"
    if k_adr: kund_info += f"<br/>{k_adr}"
    if k_post or k_ort: kund_info += f"<br/>{k_post} {k_ort}".strip()

    faktura_info = f"<b>FAKTURAADRESS:</b><br/>{f_namn}"
    if f_adr: faktura_info += f"<br/>{f_adr}"
    if f_post or f_ort: faktura_info += f"<br/>{f_post} {f_ort}".strip()

    address_table = Table([[Paragraph(kund_info, meta_style), Paragraph(faktura_info, meta_style)]], colWidths=[9*cm, 9*cm])
    address_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(address_table)
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CBD5E1"), spaceBefore=8, spaceAfter=12))

    table_data = [[
        Paragraph("<b>Datum</b>", meta_bold),
        Paragraph("<b>Artikel / Åtgärd / Beskrivning</b>", meta_bold),
        Paragraph("<b>Antal/Enh</b>", meta_bold),
        Paragraph("<b>A-pris</b>", meta_bold),
        Paragraph("<b>Belopp (SEK)</b>", meta_bold)
    ]]

    totalt_belopp, totalt_timmar = 0.0, 0.0
    for _, row in records.sort_values(by="Datum").iterrows():
        try: t_tim, t_pris, t_tot = float(row["Timmar"]), float(row["Timpris"]), float(row["Totalt"])
        except ValueError: t_tim, t_pris, t_tot = 0.0, 0.0, 0.0
        totalt_belopp += t_tot
        totalt_timmar += t_tim

        art_nr = clean_str(row['Artikelnr'])
        art_nr_str = f"[{art_nr}] " if art_nr else ""
        desc_str = clean_str(row['Beskrivning'])
        desc = f"<br/><i>{desc_str}</i>" if desc_str else ""
        beskrivning_text = f"<b>{art_nr_str}{clean_str(row['Artikel'])}</b>{desc}"

        table_data.append([
            Paragraph(str(row["Datum"]), meta_style),
            Paragraph(beskrivning_text, meta_style),
            Paragraph(f"{int(t_tim) if t_tim.is_integer() else t_tim}", meta_style),
            Paragraph(f"{t_pris:.2f} kr", meta_style),
            Paragraph(f"{t_tot:.2f} kr", meta_style)
        ])

    table_data.append([
        Paragraph("<b>Totalt:</b>", meta_bold), Paragraph("", meta_style),
        Paragraph(f"<b>{int(totalt_timmar) if totalt_timmar.is_integer() else totalt_timmar} st/h</b>", meta_bold), Paragraph("", meta_style),
        Paragraph(f"<b>{totalt_belopp:.2f} kr</b>", meta_bold)
    ])

    t = Table(table_data, colWidths=[2.5*cm, 8.5*cm, 2.2*cm, 2.3*cm, 2.5*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#F1F5F9")),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5), ('TOPPADDING', (0,0), (-1,-1), 5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('VALIGN', (0,0), (-1,-1), 'TOP'), ('ALIGN', (2,0), (-1,-1), 'RIGHT'),
        ('BACKGROUND', (0,-1), (-1,-1), colors.HexColor("#E2E8F0")),
    ]))

    story.append(t)
    doc.build(story)
    return True

# --- SESSION STATE INITIALISERING ---
if "temp_items" not in st.session_state:
    st.session_state.temp_items = []

df_data = load_data()
df_art = load_articles()

st.title("💼 Laso Invest AB – Tid & Fakturering")

tabs = st.tabs(["➕ Registrera arbete", "📦 Artikeldatabas", "✏️ Redigera / Ta bort", "📄 Fakturaunderlag"])

# ==========================================
# FLIK 1: REGISTRERA ARBETE
# ==========================================
with tabs[0]:
    st.subheader("1. Kund & Fakturauppgifter")
    col1, col2 = st.columns(2)
    
    with col1:
        k_orgnr = st.text_input("Personnr / Org.nr", key="k_orgnr")
        k_namn = st.text_input("Kundnamn *", key="k_namn")
        k_adress = st.text_input("Kund Adress", key="k_adress")
        k_postnr = st.text_input("Kund Postnr", key="k_postnr")
        k_ort = st.text_input("Kund Ort", key="k_ort")

    with col2:
        f_namn = st.text_input("Fakturanamn (Om annan)", key="f_namn")
        f_adress = st.text_input("Fakturaadress", key="f_adress")
        f_postnr = st.text_input("Faktura Postnr", key="f_postnr")
        f_ort = st.text_input("Faktura Ort", key="f_ort")

    # 2. Lägg till artikel/åtgärd
    st.divider()
    st.subheader("2. Lägg till artikel/åtgärd")

    # Bygg listan med tydliga kategorirubriker
    art_options = ["-- Välj artikel --"]
    art_map = {}

    # Gruppera artiklarna per kategori
    for kat, group in df_art.groupby("Kategori", sort=False):
        # Lägg till kategorin som en synlig rubrik i listan
        rubrik = f"─── 📂 {kat.upper()} ───"
        art_options.append(rubrik)
        
        # Lägg till alla artiklar under denna kategori
        for _, r in group.iterrows():
            display_text = f"   {r['Artikel']} ({r['ArtPris']} kr)"
            art_options.append(display_text)
            art_map[display_text] = r

    col_a, col_b, col_c, col_d = st.columns([2, 4, 2, 4])
    with col_a:
        datum_val = st.date_input("Datum", value=date.today())
    with col_b:
        val_art = st.selectbox("Välj Artikel", options=art_options, index=0)
    with col_c:
        antal_val = st.number_input("Antal/Timmar", min_value=0.5, value=1.0, step=0.5)
    with col_d:
        desc_val = st.text_input("Beskrivning (frivillig)", key="ent_desc_val")

    if st.button("➕ Lägg till rad i underlag"):
        # Kontrollera att man inte valt förvalet eller en kategorirubrik
        if val_art == "-- Välj artikel --":
            st.warning("Du måste välja en artikel från listan!")
        elif val_art.startswith("───"):
            st.warning("Det där är en kategorirubrik. Välj en artikel under rubriken!")
        else:
            art_row = art_map[val_art]
            pris = float(art_row["ArtPris"])
            tot = float(antal_val) * pris

            st.session_state.temp_items.append({
                "Datum": str(datum_val),
                "Artikelnr": art_row["Artikelnr"],
                "Artikel": art_row["Artikel"],
                "Kategori": art_row["Kategori"],
                "Beskrivning": desc_val,
                "Timmar": int(antal_val) if float(antal_val).is_integer() else antal_val,
                "Timpris": pris,
                "Totalt": tot
            })
            st.success(f"Lade till: {art_row['Artikel']}")
            st.rerun()

    # Visa tillagda rader
    if st.session_state.temp_items:
        st.markdown("### Tillagda rader för detta underlag:")
        temp_df = pd.DataFrame(st.session_state.temp_items)
        st.dataframe(temp_df[["Datum", "Artikelnr", "Artikel", "Beskrivning", "Timmar", "Timpris", "Totalt"]], use_container_width=True)

        if st.button("❌ Töm underlagets rader"):
            st.session_state.temp_items = []
            st.rerun()

        st.divider()
        if st.button("💾 SPARA HELA UNDERLAGET TILL KUND", type="primary", use_container_width=True):
            if not k_namn.strip():
                st.error("Du måste fylla i Kundnamn!")
            else:
                start_id = 1
                if not df_data.empty:
                    try: start_id = int(pd.to_numeric(df_data["ID"]).max() + 1)
                    except Exception: start_id = len(df_data) + 1

                new_rows = []
                for idx, item in enumerate(st.session_state.temp_items):
                    new_rows.append({
                        "ID": str(start_id + idx),
                        "Datum": item["Datum"],
                        "Artikelnr": item["Artikelnr"],
                        "Artikel": item["Artikel"],
                        "Kategori": item["Kategori"],
                        "Kund_OrgNr": k_orgnr,
                        "Kund_Namn": k_namn,
                        "Kund_Adress": k_adress,
                        "Kund_Postnr": k_postnr,
                        "Kund_Ort": k_ort,
                        "Faktura_Namn": f_namn,
                        "Faktura_Adress": f_adress,
                        "Faktura_Postnr": f_postnr,
                        "Faktura_Ort": f_ort,
                        "Beskrivning": item["Beskrivning"],
                        "Timmar": str(item["Timmar"]),
                        "Timpris": str(item["Timpris"]),
                        "Totalt": str(item["Totalt"])
                    })

                df_data = pd.concat([df_data, pd.DataFrame(new_rows)], ignore_index=True)
                save_data(df_data)
                st.session_state.temp_items = []
                st.success(f"Underlaget för {k_namn} har sparats!")
                st.rerun()

# ==========================================
# FLIK 2: ARTIKELDATABAS
# ==========================================
with tabs[1]:
    st.subheader("Hantera Artikeldatabas")
    col_left, col_right = st.columns([1, 2])

    with col_left:
        st.markdown("#### Lägg till / Ändra pris")
        cat_art = st.selectbox("Kategori", options=["Grävmaskin Volvo 50D", "Traktor Lundberg 6240", "Övrigt"])
        nr_art = st.text_input("Artikelnr")
        namn_art = st.text_input("Artikelnamn")
        pris_art = st.text_input("Pris (SEK)")

        if st.button("💾 Spara / Uppdatera Artikel"):
            if nr_art and namn_art and pris_art:
                idx = df_art[df_art["Artikelnr"] == nr_art].index
                if not idx.empty:
                    df_art.loc[idx, "Kategori"] = cat_art
                    df_art.loc[idx, "Artikel"] = namn_art
                    df_art.loc[idx, "ArtPris"] = pris_art
                else:
                    new_art = pd.DataFrame([{"Kategori": cat_art, "Artikelnr": nr_art, "Artikel": namn_art, "ArtPris": pris_art}])
                    df_art = pd.concat([df_art, new_art], ignore_index=True)
                save_articles(df_art)
                st.success("Artikeln uppdaterades!")
                st.rerun()
            else:
                st.warning("Fyll i alla fält.")

    with col_right:
        st.markdown("#### Sparade artiklar")
        st.dataframe(df_art, use_container_width=True, height=400)

        art_to_del = st.selectbox("Ta bort artikel:", options=[""] + list(df_art["Artikelnr"].unique()))
        if st.button("❌ Ta bort vald artikel"):
            if art_to_del:
                df_art = df_art[df_art["Artikelnr"] != art_to_del]
                save_articles(df_art)
                st.success(f"Artikel {art_to_del} raderades!")
                st.rerun()

# ==========================================
# FLIK 3: REDIGERA / TA BORT POSTER
# ==========================================
with tabs[2]:
    st.subheader("Registrerade poster i databasen")
    if df_data.empty:
        st.info("Inga poster sparade ännu.")
    else:
        st.dataframe(df_data[["ID", "Datum", "Kund_Namn", "Artikelnr", "Artikel", "Beskrivning", "Timmar", "Totalt"]], use_container_width=True)

        st.divider()
        col_del1, col_del2 = st.columns(2)
        with col_del1:
            id_to_del = st.selectbox("Välj ID att radera:", options=[""] + list(df_data["ID"].unique()))
            if st.button("❌ Radera vald rad"):
                if id_to_del:
                    df_data = df_data[df_data["ID"] != id_to_del]
                    save_data(df_data)
                    st.success(f"Rad {id_to_del} raderades!")
                    st.rerun()

# ==========================================
# FLIK 4: FAKTURAUNDERLAG (PDF)
# ==========================================
with tabs[3]:
    st.subheader("Skapa PDF-Fakturaunderlag")
    
    # 1. Ladda om databasen direkt så att nyligen tillagda kunder syns direkt
    df_fresh = load_data()
    
    if df_fresh.empty:
        st.info("Inga registrerade underlag finns ännu.")
    else:
        # 2. Hämta alla unika kundnamn, rensa tomma rader och sortera i bokstavsordning
        kunder = sorted(list(set(clean_str(k) for k in df_fresh["Kund_Namn"].unique() if clean_str(k) != "")))
        
        if not kunder:
            st.info("Inga registrerade kunder hittades.")
        else:
            val_kund = st.selectbox("Välj Kund:", options=kunder)
            kund_df = df_fresh[df_fresh["Kund_Namn"] == val_kund]

            pdf_filename = f"Fakturaunderlag_{val_kund}_{date.today()}.pdf"

            if st.button("📄 Generera PDF-Fakturaunderlag", type="primary"):
                if generate_pdf_file(val_kund, kund_df, pdf_filename):
                    st.success("PDF skapades framgångsrikt!")
                    with open(pdf_filename, "rb") as f:
                        st.download_button(
                            label="⬇️ Ladda ner PDF",
                            data=f,
                            file_name=pdf_filename,
                            mime="application/pdf"
                        )
