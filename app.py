import streamlit as st
import pandas as pd
import os
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
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
LOGO_FILE = "logo.png"

# --- LADDA & SPARA DATA ---
def load_data(file_path, columns):
    if os.path.exists(file_path):
        try:
            df = pd.read_csv(file_path)
            if not df.empty:
                return df
        except:
            pass
    return pd.DataFrame(columns=columns)

def save_data(df, file_path):
    df.to_csv(file_path, index=False)

# Initiera filer om de saknas
if not os.path.exists(ARTIKLAR_FILE):
    df_artiklar = pd.DataFrame([
        {"Artikel": "Traktortimmar - Lundberg 343", "Enhet": "tim", "A-pris": 850.0},
        {"Artikel": "Maskintjänst / Förare", "Enhet": "tim", "A-pris": 550.0},
        {"Artikel": "Etablering / Framkörning", "Enhet": "st", "A-pris": 1200.0}
    ])
    save_data(df_artiklar, ARTIKLAR_FILE)
else:
    df_artiklar = load_data(ARTIKLAR_FILE, ["Artikel", "Enhet", "A-pris"])

df_fakturor = load_data(DATA_FILE, ["Fakturanummer", "Kund", "Adress", "Fakturaadress", "E-post", "Datum", "Projekt", "Artiklar_JSON", "Totalt"])
df_offerter = load_data(OFFERTER_FILE, ["Offertnummer", "Kund", "Adress", "E-post", "Datum", "Giltig_till", "Projekt", "Artiklar_JSON", "Totalt", "Villkor"])

# Säker hämtning av artikelinfo
def get_article_info(df, article_name):
    if not article_name or article_name == "--- Välj artikel ---" or df.empty or "Artikel" not in df.columns:
        return 0.0, "st"
    selected = df[df["Artikel"] == article_name]
    if selected.empty:
        return 0.0, "st"

    pris = 0.0
    for col in ["A-pris", "Pris", "A_pris", "a-pris"]:
        if col in selected.columns:
            try:
                pris = float(selected[col].values[0])
                break
            except:
                pass

    enhet = "st"
    if "Enhet" in selected.columns:
        enhet = str(selected["Enhet"].values[0])

    return pris, enhet

# --- PDF GENERERING ---
def generate_pdf(doc_type, doc_num, kund, adress, fakturaadress, datum, extra_date, projekt, items, totalt, villkor=""):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=30, leftMargin=30, topMargin=30, bottomMargin=30)
    story = []
    styles = getSampleStyleSheet()

    normal_style = styles['Normal']
    bold_style = ParagraphStyle('BoldText', parent=normal_style, fontName='Helvetica-Bold')

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

    info_data = [
        [Paragraph("<b>Kund:</b>", normal_style), Paragraph(kund, normal_style)],
        [Paragraph("<b>Adress:</b>", normal_style), Paragraph(adress if adress else "-", normal_style)],
        [Paragraph("<b>Fakturaadress / E-post:</b>", normal_style), Paragraph(fakturaadress if fakturaadress else "-", normal_style)],
        [Paragraph("<b>Projekt / Anmärkning:</b>", normal_style), Paragraph(projekt if projekt else "-", normal_style)]
    ]
    info_table = Table(info_data, colWidths=[140, 360])
    info_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP')]))
    story.append(info_table)
    story.append(Spacer(1, 20))

    table_data = [["Beskrivning / Artikel", "Antal", "Enhet", "A-pris (kr)", "Summa (kr)"]]
    for item in items:
        table_data.append([
            item["Artikel"],
            f"{int(item['Antal'])}",
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

    if villkor:
        story.append(Spacer(1, 20))
        story.append(Paragraph("<b>Villkor & Information:</b>", bold_style))
        story.append(Paragraph(villkor.replace("\n", "<br/>"), normal_style))

    doc.build(story)
    buffer.seek(0)
    return buffer

# --- FUNKTION FÖR E-POST ---
def send_email_with_pdf(to_email, subject, body, pdf_buffer, filename):
    smtp_server = st.secrets.get("SMTP_SERVER", "")
    smtp_port = st.secrets.get("SMTP_PORT", 587)
    smtp_user = st.secrets.get("SMTP_USER", "")
    smtp_pass = st.secrets.get("SMTP_PASSWORD", "")

    if not smtp_server or not smtp_user:
        st.error("E-postinställningar saknas i Streamlit Secrets (SMTP)!")
        return False

    msg = MIMEMultipart()
    msg['From'] = smtp_user
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    attachment = MIMEApplication(pdf_buffer.getvalue(), Name=filename)
    attachment['Content-Disposition'] = f'attachment; filename="{filename}"'
    msg.attach(attachment)

    try:
        server = smtplib.SMTP(smtp_server, int(smtp_port))
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()
        return True
    except Exception as e:
        st.error(f"Kunde inte skicka e-post: {e}")
        return False

# --- UI APP LAYOUT ---
st.title("🚜 Laso Invest AB - System")

tab1, tab2, tab3 = st.tabs(["📄 Fakturaunderlag", "📋 Skapa Offert", "⚙️ Artikelregister"])

# Skapa artikellista med "--- Välj artikel ---" högst upp
raw_artiklar = df_artiklar["Artikel"].tolist() if "Artikel" in df_artiklar.columns else []
artiklar_lista = ["--- Välj artikel ---"] + [a for a in raw_artiklar if a != "--- Välj artikel ---"]

# --- FLIK 1: FAKTURUNDERLAG ---
with tab1:
    st.header("Nytt Fakturaunderlag")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        f_kund = st.text_input("Kundnamn", key="f_kund")
        f_adress = st.text_input("Adress", key="f_adress")
    with col2:
        f_fakturaadress = st.text_input("Fakturaadress / E-post", key="f_fakturaadress")
        f_projekt = st.text_input("Projekt / Anmärkning", key="f_projekt")
    with col3:
        f_nr = st.text_input("Fakturanummer / Referens", value=f"F-{datetime.now().strftime('%Y%m%d%H%M')}", key="f_nr")
        f_datum = st.date_input("Datum", key="f_datum")

    st.subheader("Artiklar på fakturan")
    if "f_rows" not in st.session_state:
        st.session_state.f_rows = [{"Artikel": "--- Välj artikel ---", "Antal": 1, "A-pris": 0.0, "Enhet": "tim"}]

    def add_f_row():
        st.session_state.f_rows.append({"Artikel": "--- Välj artikel ---", "Antal": 1, "A-pris": 0.0, "Enhet": "tim"})

    f_items = []
    f_totalt = 0.0

    for i, row in enumerate(st.session_state.f_rows):
        c1, c2, c3, c4, c5 = st.columns([3, 1, 1, 1, 1])
        with c1:
            art = st.selectbox(f"Artikel #{i+1}", artiklar_lista, key=f"f_art_{i}")
            default_pris, default_enhet = get_article_info(df_artiklar, art)
        with c2:
            antal = st.number_input("Antal", min_value=1, value=int(row["Antal"]), step=1, key=f"f_ant_{i}")
        with c3:
            enhet = st.text_input("Enhet", value=default_enhet, key=f"f_enh_{i}")
        with c4:
            pris = st.number_input("A-pris", min_value=0.0, value=float(default_pris), step=50.0, key=f"f_pris_{i}")
        with c5:
            summa = antal * pris if art != "--- Välj artikel ---" else 0.0
            st.text_input("Summa", value=f"{summa:.2f} kr", disabled=True, key=f"f_sum_{i}")
            if art != "--- Välj artikel ---":
                f_totalt += summa
                f_items.append({"Artikel": art, "Antal": int(antal), "Enhet": enhet, "A-pris": pris, "Summa": summa})

    st.button("➕ Lägg till rad", on_click=add_f_row, key="add_f")
    st.markdown(f"### Totalsumma: **{f_totalt:.2f} kr** exkl. moms")

    col_btn1, col_btn2, col_btn3 = st.columns(3)
    
    with col_btn1:
        if st.button("💾 Spara Fakturaunderlag", type="primary", use_container_width=True):
            if not f_kund:
                st.error("Mata in kundnamn!")
            else:
                new_row = {
                    "Fakturanummer": f_nr,
                    "Kund": f_kund,
                    "Adress": f_adress,
                    "Fakturaadress": f_fakturaadress,
                    "E-post": f_fakturaadress,
                    "Datum": str(f_datum),
                    "Projekt": f_projekt,
                    "Artiklar_JSON": json.dumps(f_items),
                    "Totalt": f_totalt
                }
                df_fakturor = pd.concat([df_fakturor, pd.DataFrame([new_row])], ignore_index=True)
                save_data(df_fakturor, DATA_FILE)
                st.success(f"Fakturaunderlag {f_nr} har sparats i databasen!")

    with col_btn2:
        pdf_buf = generate_pdf("Fakturaunderlag", f_nr, f_kund, f_adress, f_fakturaadress, str(f_datum), "", f_projekt, f_items, f_totalt)
        st.download_button("📥 Ladda ner PDF", data=pdf_buf, file_name=f"Fakturaunderlag_{f_nr}.pdf", mime="application/pdf", use_container_width=True)

    with col_btn3:
        if st.button("📧 Skicka via E-post", use_container_width=True):
            if not f_fakturaadress:
                st.error("Mata in e-post i fältet 'Fakturaadress / E-post' först!")
            else:
                body_text = f"Hej {f_kund},\n\nHär kommer fakturaunderlag {f_nr} gällande {f_projekt}.\n\nMed vänlig hälsning,\nLaso Invest AB"
                if send_email_with_pdf(f_fakturaadress, f"Fakturaunderlag {f_nr} - Laso Invest AB", body_text, pdf_buf, f"Fakturaunderlag_{f_nr}.pdf"):
                    st.success(f"E-post skickad till {f_fakturaadress}!")

# --- FLIK 2: SKAPA OFFERT ---
with tab2:
    st.header("Skapa Ny Offert")
    o_col1, o_col2, o_col3 = st.columns(3)
    with o_col1:
        o_kund = st.text_input("Kundnamn", key="o_kund")
        o_adress = st.text_input("Adress", key="o_adress")
    with o_col2:
        o_email = st.text_input("E-post", key="o_email")
        o_projekt = st.text_input("Projektnamn / Uppdragsbeskrivning", key="o_projekt")
    with o_col3:
        o_nr = st.text_input("Offertnummer", value=f"OFF-{datetime.now().strftime('%Y%m%d%H%M')}", key="o_nr")
        o_datum = st.date_input("Offertdatum", key="o_datum")
        o_giltig = st.date_input("Giltig t.o.m", value=datetime.now() + timedelta(days=30), key="o_giltig")

    st.subheader("Offertrader")
    if "o_rows" not in st.session_state:
        st.session_state.o_rows = [{"Artikel": "--- Välj artikel ---", "Antal": 1, "A-pris": 0.0, "Enhet": "tim"}]

    def add_o_row():
        st.session_state.o_rows.append({"Artikel": "--- Välj artikel ---", "Antal": 1, "A-pris": 0.0, "Enhet": "tim"})

    o_items = []
    o_totalt = 0.0

    for i, row in enumerate(st.session_state.o_rows):
        oc1, oc2, oc3, oc4, oc5 = st.columns([3, 1, 1, 1, 1])
        with oc1:
            o_art = st.selectbox(f"Artikel #{i+1}", artiklar_lista, key=f"o_art_{i}")
            o_default_pris, o_default_enhet = get_article_info(df_artiklar, o_art)
        with oc2:
            o_antal = st.number_input("Antal", min_value=1, value=int(row["Antal"]), step=1, key=f"o_ant_{i}")
        with oc3:
            o_enhet = st.text_input("Enhet", value=o_default_enhet, key=f"o_enh_{i}")
        with oc4:
            o_pris = st.number_input("A-pris", min_value=0.0, value=float(o_default_pris), step=50.0, key=f"o_pris_{i}")
        with oc5:
            o_summa = o_antal * o_pris if o_art != "--- Välj artikel ---" else 0.0
            st.text_input("Summa", value=f"{o_summa:.2f} kr", disabled=True, key=f"o_sum_{i}")
            if o_art != "--- Välj artikel ---":
                o_totalt += o_summa
                o_items.append({"Artikel": o_art, "Antal": int(o_antal), "Enhet": o_enhet, "A-pris": o_pris, "Summa": o_summa})

    st.button("➕ Lägg till rad", on_click=add_o_row, key="add_o")
    
    o_villkor = st.text_area("Särskilda villkor / Noteringar", value="Priser exklusive moms. Betalningsvillkor 30 dagar efter godkänd offert/slutfört arbete.", key="o_villkor")

    st.markdown(f"### Beräknat Offertvärde: **{o_totalt:.2f} kr** exkl. moms")

    col_obtn1, col_obtn2, col_obtn3 = st.columns(3)

    with col_obtn1:
        if st.button("💾 Spara Offert", type="primary", use_container_width=True):
            if not o_kund:
                st.error("Mata in kundnamn!")
            else:
                o_new_row = {
                    "Offertnummer": o_nr,
                    "Kund": o_kund,
                    "Adress": o_adress,
                    "E-post": o_email,
                    "Datum": str(o_datum),
                    "Giltig_till": str(o_giltig),
                    "Projekt": o_projekt,
                    "Artiklar_JSON": json.dumps(o_items),
                    "Totalt": o_totalt,
                    "Villkor": o_villkor
                }
                df_offerter = pd.concat([df_offerter, pd.DataFrame([o_new_row])], ignore_index=True)
                save_data(df_offerter, OFFERTER_FILE)
                st.success(f"Offert {o_nr} har sparats!")

    with col_obtn2:
        pdf_offert = generate_pdf("Offert", o_nr, o_kund, o_adress, o_email, str(o_datum), str(o_giltig), o_projekt, o_items, o_totalt, o_villkor)
        st.download_button("📥 Ladda ner Offert-PDF", data=pdf_offert, file_name=f"Offert_{o_nr}.pdf", mime="application/pdf", use_container_width=True)

    with col_obtn3:
        if st.button("📧 Skicka Offert via E-post", use_container_width=True):
            if not o_email:
                st.error("Mata in kundens e-postadress först!")
            else:
                o_body = f"Hej {o_kund},\n\nHär kommer offert {o_nr} gällande {o_projekt}.\nOfferten är giltig t.o.m. {o_giltig}.\n\nMed vänlig hälsning,\nLaso Invest AB"
                if send_email_with_pdf(o_email, f"Offert {o_nr} - Laso Invest AB", o_body, pdf_offert, f"Offert_{o_nr}.pdf"):
                    st.success(f"Offert skickad till {o_email}!")

# --- FLIK 3: ARTIKELREGISTER ---
with tab3:
    st.header("Hantera Artikelregister")
    edited_df = st.data_editor(df_artiklar, num_rows="dynamic", key="art_editor")
    if st.button("Spara ändringar i artikelregistret"):
        save_data(edited_df, ARTIKLAR_FILE)
        st.success("Artikelregistret har uppdaterats!")
