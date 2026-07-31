import streamlit as st
import pandas as pd
import os
from datetime import datetime, timedelta
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

st.set_page_config(page_title="Laso Invest AB", layout="wide")

# Filsökvägar
DATA_FILE = "laso_invest_data.csv"
ARTIKLAR_FILE = "laso_invest_artiklar.csv"
OFFERTER_FILE = "laso_invest_offerter.csv"
LOGO_FILE = "logo.png"  # Filnamn för framtida logotyp

# Ladda eller skapa data
def load_data(file_path, columns):
    if os.path.exists(file_path):
        return pd.read_csv(file_path)
    return pd.DataFrame(columns=columns)

def save_data(df, file_path):
    df.to_csv(file_path, index=False)

df_fakturor = load_data(DATA_FILE, ["Fakturanummer", "Kund", "Datum", "Projekt", "Artiklar_JSON", "Totalt"])
df_artiklar = load_data(ARTIKLAR_FILE, ["Artikel", "Enhet", "A-pris"])
df_offerter = load_data(OFFERTER_FILE, ["Offertnummer", "Kund", "Datum", "Giltig_till", "Projekt", "Artiklar_JSON", "Totalt", "Villkor"])

# Standardartiklar om listan är tom
if df_artiklar.empty:
    df_artiklar = pd.DataFrame([
        {"Artikel": "Traktortimmar - Lundberg 343", "Enhet": "tim", "A-pris": 850.0},
        {"Artikel": "Maskintjänst / Förare", "Enhet": "tim", "A-pris": 550.0},
        {"Artikel": "Etablering / Framkörning", "Enhet": "st", "A-pris": 1200.0}
    ])
    save_data(df_artiklar, ARTIKLAR_FILE)

# Funktion för PDF-generering (Faktunderlag & Offert)
def generate_pdf(doc_type, doc_num, kund, datum, extra_date, projekt, items, totalt, villkor=""):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    styles = getSampleStyleSheet()

    # Rubrikstil
    title_style = ParagraphStyle('DocTitle', parent=styles['Heading1'], fontSize=20, leading=24, textColor=colors.HexColor("#0f2a4a"))
    normal_style = styles['Normal']
    bold_style = ParagraphStyle('BoldText', parent=normal_style, fontName='Helvetica-Bold')

    # Logotyp eller Textrubrik
    if os.path.exists(LOGO_FILE):
        try:
            img = Image(LOGO_FILE, width=120, height=120)
            img.hAlign = 'LEFT'
            story.append(img)
            story.append(Spacer(1, 10))
        except:
            pass

    header_text = f"<b>LASO INVEST AB</b><br/>" \
                  f"Dokument: {doc_type.upper()}<br/>" \
                  f"{doc_type}nr: {doc_num}<br/>" \
                  f"Datum: {datum}<br/>"
    if doc_type == "Offert":
        header_text += f"Giltig t.o.m: {extra_date}<br/>"

    story.append(Paragraph(header_text, normal_style))
    story.append(Spacer(1, 15))

    # Kund & Projektinfo
    info_data = [
        [Paragraph("<b>Mottagare / Kund:</b>", normal_style), Paragraph(kund, normal_style)],
        [Paragraph("<b>Projekt / Beskrivning:</b>", normal_style), Paragraph(projekt if projekt else "-", normal_style)]
    ]
    info_table = Table(info_data, colWidths=[130, 370])
    info_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(info_table)
    story.append(Spacer(1, 20))

    # Rader / Tabell
    table_data = [["Beskrivning / Artikel", "Antal", "Enhet", "A-pris (kr)", "Summa (kr)"]]
    for item in items:
        table_data.append([
            item["Artikel"],
            f"{item['Antal']:.2f}",
            item["Enhet"],
            f"{item['A-pris']:.2f}",
            f"{item['Summa']:.2f}"
        ])
    
    table_data.append(["", "", "", "Totalt exkl. moms:", f"{totalt:.2f} kr"])

    t = Table(table_data, colWidths=[220, 60, 60, 80, 80])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#0f2a4a")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0,0), (-1,0), 6),
        ('GRID', (0,0), (-1,-2), 0.5, colors.lightgrey),
        ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
        ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
    ]))
    story.append(t)

    # Villkorstext om det finns (t.ex. för Offert)
    if villkor:
        story.append(Spacer(1, 20))
        story.append(Paragraph("<b>Villkor & Information:</b>", bold_style))
        story.append(Paragraph(villkor.replace("\n", "<br/>"), normal_style))

    doc.build(story)
    buffer.seek(0)
    return buffer

# --- APP LAYOUT ---
st.title("🚜 Laso Invest AB - System")

tab1, tab2, tab3 = st.tabs(["📄 Fakturaunderlag", "📋 Skapa Offert", "⚙️ Artikelregister"])

# --- FLIK 1: FAKTURUNDERLAG ---
with tab1:
    st.header("Nytt Fakturaunderlag")
    col1, col2, col3 = st.columns(3)
    with col1:
        f_kund = st.text_input("Kundnamn", key="f_kund")
    with col2:
        f_nr = st.text_input("Fakturanummer / Referens", value=f"F-{datetime.now().strftime('%Y%m%d%H%M')}", key="f_nr")
    with col3:
        f_datum = st.date_input("Datum", key="f_datum")

    f_projekt = st.text_input("Projekt / Anmärkning", key="f_projekt")

    st.subheader("Artiklar på fakturan")
    if "f_rows" not in st.session_state:
        st.session_state.f_rows = [{"Artikel": df_artiklar["Artikel"].iloc[0] if not df_artiklar.empty else "", "Antal": 1.0, "A-pris": 0.0, "Enhet": "tim"}]

    def add_f_row():
        st.session_state.f_rows.append({"Artikel": "", "Antal": 1.0, "A-pris": 0.0, "Enhet": "tim"})

    f_items = []
    f_totalt = 0.0

    for i, row in enumerate(st.session_state.f_rows):
        c1, c2, c3, c4, c5 = st.columns([3, 1, 1, 1, 1])
        with c1:
            art = st.selectbox(f"Artikel #{i+1}", df_artiklar["Artikel"].tolist(), key=f"f_art_{i}")
            selected_art = df_artiklar[df_artiklar["Artikel"] == art]
            default_pris = selected_art["A-pris"].values[0] if not selected_art.empty else 0.0
            default_enhet = selected_art["Enhet"].values[0] if not selected_art.empty else "st"
        with c2:
            antal = st.number_input("Antal", min_value=0.0, value=float(row["Antal"]), step=0.5, key=f"f_ant_{i}")
        with c3:
            enhet = st.text_input("Enhet", value=default_enhet, key=f"f_enh_{i}")
        with c4:
            pris = st.number_input("A-pris", min_value=0.0, value=float(default_pris), step=50.0, key=f"f_pris_{i}")
        with c5:
            summa = antal * pris
            st.text_input("Summa", value=f"{summa:.2f} kr", disabled=True, key=f"f_sum_{i}")
            f_totalt += summa
            f_items.append({"Artikel": art, "Antal": antal, "Enhet": enhet, "A-pris": pris, "Summa": summa})

    st.button("➕ Lägg till rad", on_click=add_f_row, key="add_f")
    st.markdown(f"### Totalsumma: **{f_totalt:.2f} kr** exkl. moms")

    if st.button("Generera Faktunderlag (PDF)", type="primary"):
        if not f_kund:
            st.error("Mata in kundnamn!")
        else:
            pdf_buf = generate_pdf("Fakturaunderlag", f_nr, f_kund, str(f_datum), "", f_projekt, f_items, f_totalt)
            st.download_button("💾 Ladda ner Faktunderlag-PDF", data=pdf_buf, file_name=f"Fakturaunderlag_{f_nr}.pdf", mime="application/pdf")

# --- FLIK 2: SKAPA OFFERT ---
with tab2:
    st.header("Skapa Ny Offert")
    o_col1, o_col2, o_col3, o_col4 = st.columns(4)
    with o_col1:
        o_kund = st.text_input("Kundnamn", key="o_kund")
    with o_col2:
        o_nr = st.text_input("Offertnummer", value=f"OFF-{datetime.now().strftime('%Y%m%d%H%M')}", key="o_nr")
    with o_col3:
        o_datum = st.date_input("Offertdatum", key="o_datum")
    with o_col4:
        o_giltig = st.date_input("Giltig t.o.m", value=datetime.now() + timedelta(days=30), key="o_giltig")

    o_projekt = st.text_input("Projektnamn / Uppdragsbeskrivning", key="o_projekt")

    st.subheader("Offertrader")
    if "o_rows" not in st.session_state:
        st.session_state.o_rows = [{"Artikel": df_artiklar["Artikel"].iloc[0] if not df_artiklar.empty else "", "Antal": 1.0, "A-pris": 0.0, "Enhet": "tim"}]

    def add_o_row():
        st.session_state.o_rows.append({"Artikel": "", "Antal": 1.0, "A-pris": 0.0, "Enhet": "tim"})

    o_items = []
    o_totalt = 0.0

    for i, row in enumerate(st.session_state.o_rows):
        oc1, oc2, oc3, oc4, oc5 = st.columns([3, 1, 1, 1, 1])
        with oc1:
            o_art = st.selectbox(f"Artikel #{i+1}", df_artiklar["Artikel"].tolist(), key=f"o_art_{i}")
            o_selected_art = df_artiklar[df_artiklar["Artikel"] == o_art]
            o_default_pris = o_selected_art["A-pris"].values[0] if not o_selected_art.empty else 0.0
            o_default_enhet = o_selected_art["Enhet"].values[0] if not o_selected_art.empty else "st"
        with oc2:
            o_antal = st.number_input("Antal", min_value=0.0, value=float(row["Antal"]), step=0.5, key=f"o_ant_{i}")
        with oc3:
            o_enhet = st.text_input("Enhet", value=o_default_enhet, key=f"o_enh_{i}")
        with oc4:
            o_pris = st.number_input("A-pris", min_value=0.0, value=float(o_default_pris), step=50.0, key=f"o_pris_{i}")
        with oc5:
            o_summa = o_antal * o_pris
            st.text_input("Summa", value=f"{o_summa:.2f} kr", disabled=True, key=f"o_sum_{i}")
            o_totalt += o_summa
            o_items.append({"Artikel": o_art, "Antal": o_antal, "Enhet": o_enhet, "A-pris": o_pris, "Summa": o_summa})

    st.button("➕ Lägg till rad", on_click=add_o_row, key="add_o")
    
    o_villkor = st.text_area("Särskilda villkor / Noteringar", value="Priser exklusive moms. Betalningsvillkor 30 dagar efter godkänd offert/slutfört arbete.", key="o_villkor")

    st.markdown(f"### Beräknat Offertvärde: **{o_totalt:.2f} kr** exkl. moms")

    if st.button("Generera Offert (PDF)", type="primary"):
        if not o_kund:
            st.error("Mata in kundnamn!")
        else:
            pdf_offert = generate_pdf("Offert", o_nr, o_kund, str(o_datum), str(o_giltig), o_projekt, o_items, o_totalt, o_villkor)
            st.download_button("💾 Ladda ner Offert-PDF", data=pdf_offert, file_name=f"Offert_{o_nr}.pdf", mime="application/pdf")

# --- FLIK 3: ARTIKELREGISTER ---
with tab3:
    st.header("Hantera Artikelregister")
    edited_df = st.data_editor(df_artiklar, num_rows="dynamic", key="art_editor")
    if st.button("Spara ändringar i artikelregistret"):
        save_data(edited_df, ARTIKLAR_FILE)
        st.success("Artikelregistret har uppdaterats!")
