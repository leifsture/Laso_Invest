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
