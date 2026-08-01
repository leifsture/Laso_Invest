import os
import smtplib
import pandas as pd
import streamlit as st
from datetime import date, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm

st.set_page_config(page_title="Laso Invest AB – Tid, Fakturering & Offert", page_icon="💼", layout="wide")

DATA_FILE = "laso_invest_data.csv"
ARTICLE_FILE = "laso_invest_artiklar.csv"
OFFERT_FILE = "laso_invest_offerter.csv"

DATA_COLUMNS = [
    "ID", "Datum", "Artikelnr", "Artikel", "Kategori",
    "Kund_OrgNr", "Kund_Namn", "Kund_Adress", "Kund_Postnr", "Kund_Ort",
    "Faktura_Namn", "Faktura_Adress", "Faktura_Postnr", "Faktura_Ort",
    "Beskrivning", "Timmar", "Timpris", "Totalt"
]
ARTICLE_COLUMNS = ["Kategori", "Artikelnr", "Artikel", "ArtPris"]

OFFERT_COLUMNS = [
    "Offertnr", "Offertdatum", "Giltig_Tom", "Kund_OrgNr", "Kund_Namn", 
    "Kund_Adress", "Kund_Postnr", "Kund_Ort", "Artikelnr", "Artikel", 
    "Beskrivning", "Antal", "A_Pris", "Totalt", "Status"
]

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

def format_pris(val):
    try:
        clean_val = str(val).replace("kr", "").replace(" ", "").replace(",", ".").strip()
        num = int(round(float(clean_val)))
        return f"{num:,}".replace(",", " ") + " kr"
    except (ValueError, TypeError):
        return str(val)

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
            if df.empty: return default_articles()
            return df[ARTICLE_COLUMNS]
        except Exception: return default_articles()
    return default_articles()

def save_articles(df): df.to_csv(ARTICLE_FILE, index=False)

def load_offerter():
    if os.path.exists(OFFERT_FILE):
        try:
            df = pd.read_csv(OFFERT_FILE, dtype=str).fillna("")
            for col in OFFERT_COLUMNS:
                if col not in df.columns: df[col] = ""
            return df[OFFERT_COLUMNS]
        except Exception: return pd.DataFrame(columns=OFFERT_COLUMNS)
    return pd.DataFrame(columns=OFFERT_COLUMNS)

def save_offerter(df): df.to_csv(OFFERT_FILE, index=False)

# --- PDF FUNKTIONER ---
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
        Paragraph("<b>LASO INVEST AB</b><br/>Fakturaunderlag", title_style),
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
        Paragraph("<b>Antal/Timmar</b>", meta_bold),
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

def generate_offert_pdf(offertnr, records, filepath):
    if records is None or len(records) == 0: return False
    doc = SimpleDocTemplate(filepath, pagesize=A4, rightMargin=1.5*cm, leftMargin=1.5*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)
    story = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle("OffertTitle", parent=styles["Heading1"], fontSize=22, textColor=colors.HexColor("#2B6CB0"))
    meta_style = ParagraphStyle("MetaText", parent=styles["Normal"], fontSize=9, leading=13)
    meta_bold = ParagraphStyle("MetaTextBold", parent=styles["Normal"], fontSize=9, leading=13, fontName="Helvetica-Bold")

    first_rec = records.iloc[0]
    
    header_data = [[
        Paragraph("<b>LASO INVEST AB</b><br/><font size=14 color='#2B6CB0'><b>OFFERT</b></font>", title_style),
        Paragraph(f"<b>Offertnummer:</b> {offertnr}<br/><b>Datum:</b> {first_rec['Offertdatum']}<br/><b>Giltig t.o.m:</b> {first_rec['Giltig_Tom']}", meta_style)
    ]]
    header_table = Table(header_data, colWidths=[10*cm, 8*cm])
    header_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('ALIGN', (1,0), (1,0), 'RIGHT')]))
    story.append(header_table)
    story.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor("#2B6CB0"), spaceBefore=8, spaceAfter=12))

    k_namn, k_adr = clean_str(first_rec.get('Kund_Namn', '')), clean_str(first_rec.get('Kund_Adress', ''))
    k_post, k_ort = clean_str(first_rec.get('Kund_Postnr', '')), clean_str(first_rec.get('Kund_Ort', ''))
    k_org = clean_str(first_rec.get('Kund_OrgNr', ''))

    kund_info = f"<b>OFFERT TILL:</b><br/><b>{k_namn}</b>"
    if k_org: kund_info += f"<br/>Org.nr/Pers.nr: {k_org}"
    if k_adr: kund_info += f"<br/>{k_adr}"
    if k_post or k_ort: kund_info += f"<br/>{k_post} {k_ort}".strip()

    address_table = Table([[Paragraph(kund_info, meta_style)]], colWidths=[18*cm])
    address_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(address_table)
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CBD5E1"), spaceBefore=8, spaceAfter=12))

    table_data = [[
        Paragraph("<b>Pos</b>", meta_bold),
        Paragraph("<b>Artikel / Beskrivning</b>", meta_bold),
        Paragraph("<b>Antal/Timmar</b>", meta_bold),
        Paragraph("<b>A-pris</b>", meta_bold),
        Paragraph("<b>Totalt (exkl. moms)</b>", meta_bold)
    ]]

    totalt_exkl = 0.0
    for idx, (_, row) in enumerate(records.iterrows(), 1):
        try:
            antal = float(row["Antal"])
            apris = float(row["A_Pris"])
            tot = float(row["Totalt"])
        except ValueError:
            antal, apris, tot = 0.0, 0.0, 0.0
            
        totalt_exkl += tot

        art_nr = clean_str(row['Artikelnr'])
        art_nr_str = f"[{art_nr}] " if art_nr else ""
        desc_str = clean_str(row['Beskrivning'])
        desc = f"<br/><i>{desc_str}</i>" if desc_str else ""
        beskrivning_text = f"<b>{art_nr_str}{clean_str(row['Artikel'])}</b>{desc}"

        table_data.append([
            Paragraph(str(idx), meta_style),
            Paragraph(beskrivning_text, meta_style),
            Paragraph(f"{int(antal) if antal.is_integer() else antal}", meta_style),
            Paragraph(f"{apris:.2f} kr", meta_style),
            Paragraph(f"{tot:.2f} kr", meta_style)
        ])

    moms = totalt_exkl * 0.25
    totalt_inkl = totalt_exkl + moms

    t = Table(table_data, colWidths=[1.5*cm, 9.5*cm, 2.2*cm, 2.3*cm, 2.5*cm])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#EBF8FF")),
        ('BOTTOMPADDING', (0,0), (-1,-1), 5), ('TOPPADDING', (0,0), (-1,-1), 5),
        ('GRID', (0,0), (-1,-1), 0.5, colors.HexColor("#CBD5E1")),
        ('VALIGN', (0,0), (-1,-1), 'TOP'), ('ALIGN', (2,0), (-1,-1), 'RIGHT'),
    ]))

    story.append(t)
    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CBD5E1"), spaceBefore=10, spaceAfter=10))

    sum_data = [
        [Paragraph("Netto exkl. moms:", meta_style), Paragraph(f"{totalt_exkl:.2f} kr", meta_style)],
        [Paragraph("Moms (25%):", meta_style), Paragraph(f"{moms:.2f} kr", meta_style)],
        [Paragraph("<b>Totalt att betala:</b>", meta_bold), Paragraph(f"<b>{totalt_inkl:.2f} kr</b>", meta_bold)]
    ]
    sum_table = Table(sum_data, colWidths=[13*cm, 5*cm])
    sum_table.setStyle(TableStyle([
        ('ALIGN', (0,0), (-1,-1), 'RIGHT'),
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('BOTTOMPADDING', (0,0), (-1,-1), 3),
    ]))
    story.append(sum_table)

    story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CBD5E1"), spaceBefore=15, spaceAfter=10))
    villkor_text = f"<b>Betalningsvillkor:</b> 30 dagar netto efter slutfört arbete / fakturering.<br/>Offerten är giltig t.o.m. <b>{first_rec['Giltig_Tom']}</b>."
    story.append(Paragraph(villkor_text, meta_style))

    doc.build(story)
    return True

# --- SESSION STATE INITIALISERING ---
if "temp_items" not in st.session_state:
    st.session_state.temp_items = []

if "temp_offert_items" not in st.session_state:
    st.session_state.temp_offert_items = []

df_data = load_data()
df_art = load_articles()
df_offert = load_offerter()

st.title("💼 Laso Invest AB – Tid, Fakturering & Offert")

tabs = st.tabs(["➕ Registrera arbete", "📑 Offerter", "📦 Artikeldatabas", "✏️ Redigera / Ta bort", "📄 Fakturaunderlag"])

# ==========================================
# FLIK 1: REGISTRERA ARBETE
# ==========================================
with tabs[0]:
    st.subheader("1. Kund & Fakturauppgifter")
    col1, col2 = st.columns(2)
    
    with col1:
        k_namn = st.text_input("Kundnamn *", key="k_namn")
        k_orgnr = st.text_input("Personnr / Org.nr", key="k_orgnr")
        k_adress = st.text_input("Kund Adress", key="k_adress")
        k_postnr = st.text_input("Kund Postnr", key="k_postnr")
        k_ort = st.text_input("Kund Ort", key="k_ort")

    with col2:
        f_namn = st.text_input("Fakturanamn (Om annan)", key="f_namn")
        f_adress = st.text_input("Fakturaadress", key="f_adress")
        f_postnr = st.text_input("Faktura Postnr", key="f_postnr")
        f_ort = st.text_input("Faktura Ort", key="f_ort")

    st.divider()
    st.subheader("2. Lägg till artikel/åtgärd")

    art_options = ["-- Välj artikel --"]
    art_map = {}

    for kat, group in df_art.groupby("Kategori", sort=False):
        rubrik = f"─── 📂 {kat.upper()} ───"
        art_options.append(rubrik)
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
        if val_art == "-- Välj artikel --":
            st.warning("Du måste välja en artikel från listan!")
        elif val_art.startswith("───"):
            st.warning("Det där är en kategorirubrik. Välj en artikel under rubriken!")
        else:
            art_row = art_map[val_art]
            pris = float(art_row["ArtPris"].replace("kr", "").replace(" ", ""))
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
# FLIK 2: OFFERTER
# ==========================================
with tabs[1]:
    st.subheader("📑 Hantera & Skapa Offerter")

    sub_tab1, sub_tab2 = st.tabs(["➕ Skapa Ny Offert", "📋 Sparade Offerter"])

    with sub_tab1:
        st.markdown("#### 1. Offert- & Kundinformation")
        
        # Generera nytt offertnummer automatiskt
        next_offert_nr = "OFF-1001"
        if not df_offert.empty and "Offertnr" in df_offert.columns:
            nums = df_offert["Offertnr"].str.replace("OFF-", "", regex=False)
            nums_numeric = pd.to_numeric(nums, errors="coerce").dropna()
            if not nums_numeric.empty:
                next_offert_nr = f"OFF-{int(nums_numeric.max() + 1)}"

        # DIREKT-INMATNING AV KUNDUPPGIFTER (Ingen st.form som blockerar)
        col_off1, col_off2 = st.columns(2)
        
        with col_off1:
            off_k_namn = st.text_input("Kundnamn *", key="off_k_namn")
            off_k_orgnr = st.text_input("Org.nr / Personnr", key="off_k_orgnr")
            off_k_adress = st.text_input("Kund Adress", key="off_k_adress")
            col_p, col_o = st.columns(2)
            with col_p: off_k_post = st.text_input("Postnr", key="off_k_post")
            with col_o: off_k_ort = st.text_input("Ort", key="off_k_ort")

        with col_off2:
            offert_nr = st.text_input("Offertnummer", value=next_offert_nr, key="offert_nr")
            off_datum = st.date_input("Offertdatum", value=date.today(), key="off_datum")
            off_giltig = st.date_input("Giltig t.o.m.", value=date.today() + timedelta(days=30), key="off_giltig")

        st.divider()
        st.markdown("#### 2. Lägg till offertrader")

        art_options_off = ["-- Välj artikel --"]
        art_map_off = {}

        for kat, group in df_art.groupby("Kategori", sort=False):
            art_options_off.append(f"─── 📂 {kat.upper()} ───")
            for _, r in group.iterrows():
                display_text = f"   {r['Artikel']} ({r['ArtPris']} kr)"
                art_options_off.append(display_text)
                art_map_off[display_text] = r

        col_oa, col_ob, col_oc = st.columns([4, 2, 4])
        with col_oa:
            val_off_art = st.selectbox("Välj Artikel/Tjänst", options=art_options_off, key="val_off_art")
        with col_ob:
            off_antal = st.number_input("Antal/Timmar", min_value=0.5, value=1.0, step=0.5, key="off_antal")
        with col_oc:
            off_desc = st.text_input("Beskrivning / Specifikation (Valfri)", key="off_desc")

        if st.button("➕ Lägg till rad i offerten"):
            if val_off_art == "-- Välj artikel --" or val_off_art.startswith("───"):
                st.warning("Välj en giltig artikel ur listan!")
            else:
                art_row = art_map_off[val_off_art]
                pris = float(art_row["ArtPris"].replace("kr", "").replace(" ", ""))
                tot = float(off_antal) * pris

                st.session_state.temp_offert_items.append({
                    "Artikelnr": art_row["Artikelnr"],
                    "Artikel": art_row["Artikel"],
                    "Beskrivning": off_desc,
                    "Antal": int(off_antal) if float(off_antal).is_integer() else off_antal,
                    "A_Pris": pris,
                    "Totalt": tot
                })
                st.success(f"Lade till '{art_row['Artikel']}' i offerten.")
                st.rerun()

        # HANTERA TEMPORÄRA OFFERTRADER & BORTTAGNING AV ENSKILD RAD
        if st.session_state.temp_offert_items:
            st.markdown("##### Offertrader:")
            off_df_temp = pd.DataFrame(st.session_state.temp_offert_items)
            st.dataframe(off_df_temp, use_container_width=True)

            col_del1, col_del2, col_del3 = st.columns([2, 2, 3])
            
            with col_del1:
                # Välj vilken rad (index) som ska tas bort
                rad_options = [f"Rad {i}: {item['Artikel']}" for i, item in enumerate(st.session_state.temp_offert_items)]
                rad_att_ta_bort = st.selectbox("Välj rad att ta bort:", options=range(len(rad_options)), format_func=lambda x: rad_options[x], key="select_del_row")
            
            with col_del2:
                st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                if st.button("🗑️ Ta bort markerad rad"):
                    removed = st.session_state.temp_offert_items.pop(rad_att_ta_bort)
                    st.success(f"Tog bort '{removed['Artikel']}' från offerten.")
                    st.rerun()

            with col_del3:
                st.markdown("<div style='margin-top: 28px;'></div>", unsafe_allow_html=True)
                if st.button("❌ Töm alla offertrader"):
                    st.session_state.temp_offert_items = []
                    st.rerun()

            st.divider()
            if st.button("💾 SPARA OCH SKAPA OFFERT", type="primary", use_container_width=True):
                if not off_k_namn.strip():
                    st.error("Du måste fylla i Kundnamn!")
                else:
                    new_off_rows = []
                    for item in st.session_state.temp_offert_items:
                        new_off_rows.append({
                            "Offertnr": offert_nr,
                            "Offertdatum": str(off_datum),
                            "Giltig_Tom": str(off_giltig),
                            "Kund_OrgNr": off_k_orgnr,
                            "Kund_Namn": off_k_namn,
                            "Kund_Adress": off_k_adress,
                            "Kund_Postnr": off_k_post,
                            "Kund_Ort": off_k_ort,
                            "Artikelnr": item["Artikelnr"],
                            "Artikel": item["Artikel"],
                            "Beskrivning": item["Beskrivning"],
                            "Antal": str(item["Antal"]),
                            "A_Pris": str(item["A_Pris"]),
                            "Totalt": str(item["Totalt"]),
                            "Status": "Skapad"
                        })

                    df_offert = pd.concat([df_offert, pd.DataFrame(new_off_rows)], ignore_index=True)
                    save_offerter(df_offert)
                    st.session_state.temp_offert_items = []
                    st.success(f"Offert {offert_nr} till {off_k_namn} har sparats!")
                    st.rerun()

    # Sparade offerter
    with sub_tab2:
        df_offert_curr = load_offerter()
        if df_offert_curr.empty:
            st.info("Inga offerter har skapats ännu.")
        else:
            off_lista = df_offert_curr["Offertnr"].unique().tolist()
            val_off_nr = st.selectbox("Välj Offert för utskrift/PDF:", options=off_lista)

            selected_off_df = df_offert_curr[df_offert_curr["Offertnr"] == val_off_nr]
            st.dataframe(selected_off_df[["Offertnr", "Offertdatum", "Kund_Namn", "Artikel", "Antal", "A_Pris", "Totalt"]], use_container_width=True)

            offert_pdf_filename = f"Offert_{val_off_nr}_{selected_off_df.iloc[0]['Kund_Namn']}.pdf"

            if st.button("📄 Skapa PDF-Offert", type="primary"):
                if generate_offert_pdf(val_off_nr, selected_off_df, offert_pdf_filename):
                    st.success("Offert-PDF skapad!")
                    with open(offert_pdf_filename, "rb") as f:
                        st.download_button(
                            label="⬇️ Ladda ner Offert PDF",
                            data=f,
                            file_name=offert_pdf_filename,
                            mime="application/pdf"
                        )

# ==========================================
# FLIK 3: ARTIKELDATABAS
# ==========================================
with tabs[2]:
    st.subheader("📦 Hantera Artikeldatabas")
    
    col_tb1, col_tb2 = st.columns([2, 1])
    with col_tb1:
        st.markdown("#### Sparade artiklar (Redigera direkt i tabellen)")
        st.caption("💡 *Klicka direkt i tabellen nedan för att ändra priser, artikelnamn m.m. Klicka sedan på spara-knappen.*")
    with col_tb2:
        if st.button("🔄 Återställ till standardartiklar"):
            df_art = default_articles()
            df_art["ArtPris"] = df_art["ArtPris"].apply(format_pris)
            save_articles(df_art)
            st.success("Artikeldatabasen har återställts!")
            st.rerun()

    df_art_display = df_art.copy()
    df_art_display["ArtPris"] = df_art_display["ArtPris"].apply(format_pris)

    edited_df = st.data_editor(
        df_art_display,
        use_container_width=True,
        num_rows="dynamic",
        height=450,
        column_config={
            "Kategori": st.column_config.SelectboxColumn("Kategori", options=["Grävmaskin Volvo 50D", "Traktor Lundberg 6240", "Övrigt"], required=True),
            "Artikelnr": st.column_config.TextColumn("Artikelnr", required=True),
            "Artikel": st.column_config.TextColumn("Artikel / Benämning", required=True),
            "ArtPris": st.column_config.TextColumn("Pris", help="Anges i heltal (t.ex. 1250 kr)", required=True),
        },
        key="editor_artiklar"
    )

    if st.button("💾 Spara alla ändringar i tabellen", type="primary"):
        cleaned_df = edited_df[edited_df["Artikelnr"].astype(str).str.strip() != ""].copy()
        cleaned_df["ArtPris"] = cleaned_df["ArtPris"].apply(format_pris)
        
        save_articles(cleaned_df)
        st.success("Alla ändringar i artikeldatabasen har sparats!")
        st.rerun()

    st.divider()

    st.markdown("#### Snabbformulär: Lägg till ny artikel")
    with st.form("new_article_form"):
        col_a1, col_a2, col_a3, col_a4 = st.columns([2, 2, 3, 2])
        with col_a1:
            new_cat = st.selectbox("Kategori", options=["Grävmaskin Volvo 50D", "Traktor Lundberg 6240", "Övrigt"], key="new_cat")
        with col_a2:
            new_nr = st.text_input("Artikelnr", key="new_nr")
        with col_a3:
            new_namn = st.text_input("Artikelnamn", key="new_namn")
        with col_a4:
            new_pris = st.text_input("Pris (t.ex. 1250)", key="new_pris")

        submit_art = st.form_submit_button("➕ Lägg till ny artikel i listan")

    if submit_art:
        if new_nr and new_namn and new_pris:
            if not df_art[df_art["Artikelnr"] == new_nr].empty:
                st.error(f"Artikelnr {new_nr} finns redan!")
            else:
                formatted_p = format_pris(new_pris)
                new_row = pd.DataFrame([{"Kategori": new_cat, "Artikelnr": new_nr, "Artikel": new_namn, "ArtPris": formatted_p}])
                df_art = pd.concat([df_art, new_row], ignore_index=True)
                save_articles(df_art)
                st.success(f"Artikeln '{new_namn}' lades till med priset {formatted_p}!")
                st.rerun()
        else:
            st.warning("Fyll i alla fält för att lägga till en ny artikel.")

# ==========================================
# FLIK 4: REDIGERA / TA BORT POSTER
# ==========================================
with tabs[3]:
    st.subheader("✏️ Redigera / Ta bort registrerade poster")
    st.caption("💡 *Markera rader längst till vänster och tryck Delete för att radera. Dubbelklicka i en cell för att ändra text/priser.*")

    df_data_current = load_data()

    if df_data_current.empty:
        st.info("Inga poster sparade ännu.")
    else:
        edited_data = st.data_editor(
            df_data_current,
            use_container_width=True,
            num_rows="dynamic",
            height=500,
            column_config={
                "ID": st.column_config.TextColumn("ID", disabled=True),
                "Datum": st.column_config.TextColumn("Datum", required=True),
                "Kund_Namn": st.column_config.TextColumn("Kundnamn", required=True),
                "Artikelnr": st.column_config.TextColumn("Artikelnr"),
                "Artikel": st.column_config.TextColumn("Artikel"),
                "Beskrivning": st.column_config.TextColumn("Beskrivning"),
                "Timmar": st.column_config.TextColumn("Timmar/Antal"),
                "Timpris": st.column_config.TextColumn("A-pris"),
                "Totalt": st.column_config.TextColumn("Totalt (kr)"),
            },
            key="editor_registrerade_poster"
        )

        st.markdown("<br>", unsafe_allow_html=True)

        if st.button("💾 Spara alla ändringar i databasen", type="primary"):
            save_data(edited_data)
            st.success("Databasen har uppdaterats och sparats!")
            st.rerun()

# ==========================================
# FLIK 5: FAKTURAUNDERLAG (PDF) & E-POST
# ==========================================
with tabs[4]:
    st.subheader("Skapa PDF-Fakturaunderlag & Skicka E-post")
    
    if os.path.exists(DATA_FILE):
        df_pdf = pd.read_csv(DATA_FILE, dtype=str).fillna("")
    else:
        df_pdf = pd.DataFrame(columns=DATA_COLUMNS)

    if df_pdf.empty:
        st.info("Inga registrerade underlag finns ännu.")
    else:
        kunder_lista = list(filter(None, df_pdf["Kund_Namn"].str.strip().unique()))
        kunder_lista.sort()

        if not kunder_lista:
            st.warning("Hittade inga kunder i databasen.")
        else:
            val_kund = st.radio("Välj kund för fakturaunderlag:", options=kunder_lista, key="radio_kund_pdf")
            kund_df = df_pdf[df_pdf["Kund_Namn"].str.strip() == val_kund]

            st.write(f"**Antal rader för {val_kund}:** {len(kund_df)}")
            pdf_filename = f"Fakturaunderlag_{val_kund}_{date.today()}.pdf"

            st.divider()
            
            if st.button("📄 Generera PDF-Fakturaunderlag", type="primary"):
                if generate_pdf_file(val_kund, kund_df, pdf_filename):
                    st.success(f"PDF skapades för {val_kund}!")
                    with open(pdf_filename, "rb") as f:
                        st.download_button(
                            label="⬇️ Ladda ner PDF",
                            data=f,
                            file_name=pdf_filename,
                            mime="application/pdf"
                        )

            st.divider()
            st.subheader("✉️ Skicka underlag via E-post")
            
            with st.form("email_form"):
                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    epost_avsandare = st.text_input("Din Gmail-adress (Avsändare)", value="")
                    epost_losen = st.text_input("Ditt App-lösenord (Gmail)", type="password", help="Krävs för Gmail SMTP")
                with col_e2:
                    epost_mottagare = st.text_input("Mottagarens E-postadress")
                    epost_amne = st.text_input("Ämne", value=f"Fakturaunderlag - {val_kund}")

                epost_meddelande = st.text_area("Meddelande", value=f"Hej!\n\nHär kommer fakturaunderlaget för {val_kund}.\n\nMed vänlig hälsning,\nLaso Invest AB")

                submit_email = st.form_submit_button("✉️ Skicka E-post med PDF")

            if submit_email:
                if not os.path.exists(pdf_filename):
                    generate_pdf_file(val_kund, kund_df, pdf_filename)

                if not epost_avsandare or not epost_losen or not epost_mottagare:
                    st.error("Fyll i avsändare, lösenord och mottagare!")
                else:
                    try:
                        msg = MIMEMultipart()
                        msg['From'] = epost_avsandare
                        msg['To'] = epost_mottagare
                        msg['Subject'] = epost_amne
                        msg.attach(MIMEText(epost_meddelande, 'plain'))

                        with open(pdf_filename, "rb") as attachment:
                            part = MIMEBase('application', 'octet-stream')
                            part.set_payload(attachment.read())
                            encoders.encode_base64(part)
                            part.add_header('Content-Disposition', f"attachment; filename= {pdf_filename}")
                            msg.attach(part)

                        server = smtplib.SMTP('smtp.gmail.com', 587)
                        server.starttls()
                        server.login(epost_avsandare, epost_losen)
                        server.send_message(msg)
                        server.quit()

                        st.success(f"E-post skickades framgångsrikt till {epost_mottagare}!")
                    except Exception as e:
                        st.error(f"Kunde inte skicka e-post: {e}")
