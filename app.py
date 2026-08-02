import hashlib
import os
from datetime import date
import pandas as pd
import streamlit as st

# ==========================================
# CONSTANTS & FILE PATHS
# ==========================================
DATA_FILE = "laso_invest_data.csv"
ARTIKEL_FILE = "laso_invest_artiklar.csv"
OFFERT_FILE = "laso_invest_offerter.csv"
USER_FILE = "laso_invest_anvandare.csv"

DATA_COLUMNS = [
    "Datum",
    "Kund",
    "Adress",
    "Postnummer",
    "Ort",
    "Kategori",
    "Artikel",
    "Arbetsbeskrivning",
    "Timmar",
    "Timpris",
    "Materialkostnad",
    "Ovrigt",
    "Totalt_Exkl_Moms",
    "Moms_25",
    "Totalt_Inkl_Moms",
]

ARTIKEL_COLUMNS = ["Artikelnummer", "Artikelnamn", "Enhet", "A_Pris_Exkl_Moms"]

OFFERT_COLUMNS = [
    "Offertnummer",
    "Datum",
    "Kund",
    "Adress",
    "Postnummer",
    "Ort",
    "Kategori",
    "Beskrivning",
    "Totalt_Exkl_Moms",
    "Moms_25",
    "Totalt_Inkl_Moms",
    "Status",
]

USER_COLUMNS = ["Anvandarnamn", "Losenord_Hash", "Roll"]

KATEGORIER = ["Grävmaskin", "Traktor", "Övrigt"]


# ==========================================
# HELPER FUNCTIONS - SECURITY & USERS
# ==========================================
def hash_password(password: str) -> str:
  return hashlib.sha256(password.encode()).hexdigest()


def load_users() -> pd.DataFrame:
  if os.path.exists(USER_FILE):
    try:
      df = pd.read_csv(USER_FILE, dtype=str).fillna("")
      for col in USER_COLUMNS:
        if col not in df.columns:
          df[col] = ""
      return df[USER_COLUMNS]
    except Exception:
      pass

  default_df = pd.DataFrame([{
      "Anvandarnamn": "admin",
      "Losenord_Hash": hash_password("admin123"),
      "Roll": "admin",
  }])
  default_df.to_csv(USER_FILE, index=False)
  return default_df


def save_users(df: pd.DataFrame):
  df.to_csv(USER_FILE, index=False)


# ==========================================
# HELPER FUNCTIONS - DATA MANAGEMENT
# ==========================================
def load_data(file_path, columns) -> pd.DataFrame:
  if os.path.exists(file_path):
    try:
      df = pd.read_csv(file_path)
      for col in columns:
        if col not in df.columns:
          df[col] = 0.0 if "Pris" in col or "Totalt" in col else ""
      return df
    except Exception:
      return pd.DataFrame(columns=columns)
  return pd.DataFrame(columns=columns)


def save_data(df: pd.DataFrame, file_path):
  df.to_csv(file_path, index=False)


# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="Laso Invest AB - System", page_icon="💼", layout="wide"
)

if "logged_in" not in st.session_state:
  st.session_state.logged_in = False
if "username" not in st.session_state:
  st.session_state.username = ""
if "user_role" not in st.session_state:
  st.session_state.user_role = ""

# ==========================================
# INLOGGNINGSSKÄRM
# ==========================================
if not st.session_state.logged_in:
  st.title("💼 LASO INVEST AB")
  st.subheader("🔐 Logga in för att komma åt applikationen")

  df_users = load_users()

  col_login, _ = st.columns([1, 1])
  with col_login:
    with st.form("login_form"):
      user_input = st.text_input("Användarnamn")
      pass_input = st.text_input("Lösenord", type="password")
      submit_login = st.form_submit_button("Logga in", type="primary")

    if submit_login:
      hashed_input = hash_password(pass_input)
      user_match = df_users[
          (df_users["Anvandarnamn"].str.lower() == user_input.strip().lower())
          & (df_users["Losenord_Hash"] == hashed_input)
      ]

      if not user_match.empty:
        st.session_state.logged_in = True
        st.session_state.username = user_match.iloc[0]["Anvandarnamn"]
        st.session_state.user_role = user_match.iloc[0]["Roll"]
        st.success(f"Välkommen {st.session_state.username}!")
        st.rerun()
      else:
        st.error("Felaktigt användarnamn eller lösenord.")

  st.stop()

# ==========================================
# INLOGGAD - SIDOMENY
# ==========================================
with st.sidebar:
  st.title("💼 LASO INVEST AB")
  st.write(f"👤 Inloggad: **{st.session_state.username}**")
  st.write(f"🎭 Roll: **{st.session_state.user_role.capitalize()}**")

  if st.button("🚪 Logga ut", type="secondary"):
    st.session_state.logged_in = False
    st.session_state.username = ""
    st.session_state.user_role = ""
    st.rerun()

  st.divider()

# ==========================================
# FLIKSTRUKTUR BEROENDE PÅ ROLL
# ==========================================
tab_names = [
    "➕ Registrera arbete",
    "📑 Offerter",
    "📦 Artikeldatabas",
    "✏️ Redigera / Ta bort",
    "📄 Fakturaunderlag",
]

if st.session_state.user_role == "admin":
  tab_names.append("🔐 Admin & Användare")

tabs = st.tabs(tab_names)

# Load dataframes
df_arbeid = load_data(DATA_FILE, DATA_COLUMNS)
df_artiklar = load_data(ARTIKEL_FILE, ARTIKEL_COLUMNS)
df_offerter = load_data(OFFERT_FILE, OFFERT_COLUMNS)

# ------------------------------------------
# FLIK 0: REGISTRERA ARBETE (MED ARTIKELDATABAS)
# ------------------------------------------
with tabs[0]:
  st.header("➕ Registrera utfört arbete & material")

  # Förbered artikellista för dropdown
  artiklar_lista = ["-- Ingen / Manuell --"]
  if not df_artiklar.empty and "Artikelnamn" in df_artiklar.columns:
    artiklar_lista += df_artiklar["Artikelnamn"].tolist()

  # Välj artikel utanför formuläret för direkt prisuppdatering
  valdal_artikel = st.selectbox("Välj artikel från databasen (fyller i pris automatiskt)", artiklar_lista)
  
  default_pris = 500.0
  if valdal_artikel != "-- Ingen / Manuell --":
    art_row = df_artiklar[df_artiklar["Artikelnamn"] == valdal_artikel]
    if not art_row.empty:
      default_pris = float(art_row.iloc[0]["A_Pris_Exkl_Moms"])

  with st.form("registrerings_form", clear_on_submit=True):
    col1, col2 = st.columns(2)

    with col1:
      valth_datum = st.date_input("Datum", date.today())
      kund_namn = st.text_input("Kundnamn / Företag")
      kund_adress = st.text_input("Gatuadress")
      
      col_p1, col_p2 = st.columns(2)
      with col_p1:
        kund_postnr = st.text_input("Postnummer")
      with col_p2:
        kund_ort = st.text_input("Ort")
        
      kategori = st.selectbox("Kategori", KATEGORIER)
      arbets_beskrivning = st.text_area("Arbetsbeskrivning")

    with col2:
      timmar = st.number_input("Antal timmar", min_value=0.0, step=0.5)
      timpris = st.number_input("Timpris / A-Pris (exkl. moms)", min_value=0.0, value=default_pris, step=50.0)
      material_kostnad = st.number_input("Materialkostnad (exkl. moms)", min_value=0.0, step=100.0)
      ovrigt_kostnad = st.number_input("Övriga kostnader (exkl. moms)", min_value=0.0, step=50.0)

    submitted = st.form_submit_button("Spara registrering", type="primary")

    if submitted:
      totalt_exkl = (timmar * timpris) + material_kostnad + ovrigt_kostnad
      moms = totalt_exkl * 0.25
      totalt_inkl = totalt_exkl + moms

      ny_rad = pd.DataFrame([{
          "Datum": str(valth_datum),
          "Kund": kund_namn,
          "Adress": kund_adress,
          "Postnummer": kund_postnr,
          "Ort": kund_ort,
          "Kategori": kategori,
          "Artikel": valdal_artikel if valdal_artikel != "-- Ingen / Manuell --" else "",
          "Arbetsbeskrivning": arbets_beskrivning,
          "Timmar": timmar,
          "Timpris": timpris,
          "Materialkostnad": material_kostnad,
          "Ovrigt": ovrigt_kostnad,
          "Totalt_Exkl_Moms": totalt_exkl,
          "Moms_25": moms,
          "Totalt_Inkl_Moms": totalt_inkl
      }])

      df_arbeid = pd.concat([df_arbeid, ny_rad], ignore_index=True)
      save_data(df_arbeid, DATA_FILE)
      st.success("Registreringen har sparats!")
      st.rerun()

# ==========================================
# FLIK 1: REGISTRERA ARBETE
# ==========================================
with tabs[0]:
    st.subheader("1. Kund & Fakturauppgifter")
    
    fc = st.session_state.get("form_counter", 0)

    col1, col2 = st.columns(2)
    with col1:
        k_namn = st.text_input("Kundnamn *", key=f"k_namn_{fc}")
        k_orgnr = st.text_input("Personnr / Org.nr", key=f"k_orgnr_{fc}")
        k_adress = st.text_input("Kund Adress", key=f"k_adress_{fc}")
        k_postnr = st.text_input("Kund Postnr", key=f"k_postnr_{fc}")
        k_ort = st.text_input("Kund Ort", key=f"k_ort_{fc}")

    with col2:
        f_namn = st.text_input("Fakturanamn (Om annan)", key=f"f_namn_{fc}")
        f_adress = st.text_input("Fakturaadress", key=f"f_adress_{fc}")
        f_postnr = st.text_input("Faktura Postnr", key=f"f_postnr_{fc}")
        f_ort = st.text_input("Faktura Ort", key=f"f_ort_{fc}")

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
        datum_val = st.date_input("Datum", value=date.today(), key=f"datum_{fc}")
    with col_b:
        val_art = st.selectbox("Välj Artikel", options=art_options, index=0, key=f"art_{fc}")
    with col_c:
        antal_val = st.number_input("Antal/Timmar", min_value=1, value=1, step=1, key=f"antal_{fc}")
    with col_d:
        desc_val = st.text_input("Beskrivning (frivillig)", key=f"desc_{fc}")

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
                "Timmar": int(antal_val),
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

                idag_str = str(date.today())
                new_rows = []
                for idx, item in enumerate(st.session_state.temp_items):
                    new_rows.append({
                        "ID": str(start_id + idx),
                        "Datum": item["Datum"],
                        "Skapad_Datum": idag_str,
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
                        "Totalt": str(item["Timmar"] * item["Timpris"])
                    })

                df_data = pd.concat([df_data, pd.DataFrame(new_rows)], ignore_index=True)
                save_data(df_data)
                
                st.session_state.temp_items = []
                st.session_state.form_counter = st.session_state.get("form_counter", 0) + 1
                st.success(f"Underlaget för {k_namn} har sparats och formuläret har rensats!")
                st.rerun()

# ==========================================
# FLIK 2: OFFERTER
# ==========================================
with tabs[1]:
    st.subheader("📑 Hantera & Skapa Offerter")

    sub_tab1, sub_tab2 = st.tabs(["➕ Skapa Ny Offert", "📋 Sparade Offerter"])

    with sub_tab1:
        st.markdown("#### 1. Offert- & Kundinformation")
        
        ofc = st.session_state.get("offert_form_counter", 0)

        next_offert_nr = "OFF-1001"
        if not df_offert.empty and "Offertnr" in df_offert.columns:
            nums = df_offert["Offertnr"].str.replace("OFF-", "", regex=False)
            nums_numeric = pd.to_numeric(nums, errors="coerce").dropna()
            if not nums_numeric.empty:
                next_offert_nr = f"OFF-{int(nums_numeric.max() + 1)}"

        col_off1, col_off2 = st.columns(2)
        
        with col_off1:
            off_k_namn = st.text_input("Kundnamn *", key=f"off_k_namn_{ofc}")
            off_k_orgnr = st.text_input("Org.nr / Personnr", key=f"off_k_orgnr_{ofc}")
            off_k_adress = st.text_input("Kund Adress", key=f"off_k_adress_{ofc}")
            col_p, col_o = st.columns(2)
            with col_p: off_k_post = st.text_input("Postnr", key=f"off_k_post_{ofc}")
            with col_o: off_k_ort = st.text_input("Ort", key=f"off_k_ort_{ofc}")

        with col_off2:
            offert_nr = st.text_input("Offertnummer", value=next_offert_nr, key=f"offert_nr_{ofc}")
            off_datum = st.date_input("Offertdatum", value=date.today(), key=f"off_datum_{ofc}")
            off_giltig = st.date_input("Giltig t.o.m.", value=date.today() + timedelta(days=30), key=f"off_giltig_{ofc}")

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
            val_off_art = st.selectbox("Välj Artikel/Tjänst", options=art_options_off, key=f"val_off_art_{ofc}")
        with col_ob:
            off_antal = st.number_input("Antal/Timmar", min_value=1, value=1, step=1, key=f"off_antal_{ofc}")
        with col_oc:
            off_desc = st.text_input("Beskrivning / Specifikation (Valfri)", key=f"off_desc_{ofc}")

        if st.button("➕ Lägg till rad i offerten"):
            if val_off_art == "-- Välj artikel --" or val_off_art.startswith("───"):
                st.warning("Välj en giltig artikel ur listan!")
            else:
                art_row = art_map_off[val_off_art]
                pris = float(art_row["ArtPris"].replace("kr", "").replace(" ", ""))
                tot = int(off_antal) * pris

                st.session_state.temp_offert_items.append({
                    "Artikelnr": art_row["Artikelnr"],
                    "Artikel": art_row["Artikel"],
                    "Beskrivning": off_desc,
                    "Antal": int(off_antal),
                    "A_Pris": pris,
                    "Totalt": tot
                })
                st.success(f"Lade till '{art_row['Artikel']}' i offerten.")
                st.rerun()

        if st.session_state.temp_offert_items:
            st.markdown("##### Offertrader:")
            st.caption("💡 *Ändra Antal direkt i tabellen så räknas Totalt om automatiskt.*")

            off_df_temp = pd.DataFrame(st.session_state.temp_offert_items)
            
            off_df_temp["Antal"] = pd.to_numeric(off_df_temp["Antal"], errors="coerce").fillna(1).astype(int)
            off_df_temp["A_Pris"] = pd.to_numeric(off_df_temp["A_Pris"], errors="coerce").fillna(0.0)
            off_df_temp["Totalt"] = off_df_temp["Antal"] * off_df_temp["A_Pris"]

            edited_off_df = st.data_editor(
                off_df_temp,
                use_container_width=True,
                num_rows="dynamic",
                column_config={
                    "Artikelnr": st.column_config.TextColumn("Artikelnr"),
                    "Artikel": st.column_config.TextColumn("Artikel"),
                    "Beskrivning": st.column_config.TextColumn("Beskrivning"),
                    "Antal": st.column_config.NumberColumn("Antal/Timmar", step=1, format="%d"),
                    "A_Pris": st.column_config.NumberColumn("A-pris", format="%.2f kr"),
                    "Totalt": st.column_config.NumberColumn("Totalt", format="%.2f kr", disabled=True),
                },
                key=f"editor_temp_offert_{ofc}"
            )

            edited_off_df["Antal"] = pd.to_numeric(edited_off_df["Antal"], errors="coerce").fillna(1).astype(int)
            edited_off_df["A_Pris"] = pd.to_numeric(edited_off_df["A_Pris"], errors="coerce").fillna(0.0)
            edited_off_df["Totalt"] = edited_off_df["Antal"] * edited_off_df["A_Pris"]
            
            st.session_state.temp_offert_items = edited_off_df.to_dict(orient="records")

            if st.button("❌ Töm alla offertrader"):
                st.session_state.temp_offert_items = []
                st.rerun()

            st.divider()
            if st.button("💾 SPARA OCH SKAPA OFFERT", type="primary", use_container_width=True):
                if not off_k_namn.strip():
                    st.error("Du måste fylla i Kundnamn!")
                elif not st.session_state.temp_offert_items:
                    st.error("Du har inga offertrader kvar i listan!")
                else:
                    new_off_rows = []
                    for item in st.session_state.temp_offert_items:
                        antal_int = int(float(item["Antal"]))
                        apris_flt = float(item["A_Pris"])
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
                            "Antal": str(antal_int),
                            "A_Pris": str(apris_flt),
                            "Totalt": str(antal_int * apris_flt),
                            "Status": "Skapad"
                        })

                    df_offert = pd.concat([df_offert, pd.DataFrame(new_off_rows)], ignore_index=True)
                    save_offerter(df_offert)
                    
                    st.session_state.temp_offert_items = []
                    st.session_state.offert_form_counter = st.session_state.get("offert_form_counter", 0) + 1
                    
                    st.success(f"Offert {offert_nr} till {off_k_namn} har sparats och formuläret har rensats!")
                    st.rerun()

    with sub_tab2:
        df_offert_curr = load_offerter()
        if df_offert_curr.empty:
            st.info("Inga offerter har skapats ännu.")
        else:
            # Gruppera per offertnummer
            grouped_off = list(df_offert_curr.groupby("Offertnr", sort=False))
            
            # Hjälpfunktion för att sortera fallande baserat på det numeriska värdet i "OFF-XXXX"
            def get_offert_num(item):
                off_nr = item[0]
                num_part = str(off_nr).replace("OFF-", "")
                try:
                    return int(num_part)
                except ValueError:
                    return 0

            # Sortera fallande så högsta offertnamnet (senaste) hamnar först
            grouped_off_sorted = sorted(grouped_off, key=get_offert_num, reverse=True)

            off_options_map = {}
            for off_nr, group in grouped_off_sorted:
                kunder = group["Kund_Namn"].unique()
                k_str = ", ".join([k for k in kunder if k.strip()]) or "Okänd kund"
                label = f"{off_nr} – {k_str}"
                off_options_map[label] = off_nr

            selected_label = st.selectbox("Välj Offert för utskrift/PDF:", options=list(off_options_map.keys()))
            val_off_nr = off_options_map[selected_label]

            selected_off_df = df_offert_curr[df_offert_curr["Offertnr"] == val_off_nr].copy()
            selected_off_df["Antal_num"] = pd.to_numeric(selected_off_df["Antal"], errors="coerce").fillna(0)
            selected_off_df["A_Pris_num"] = pd.to_numeric(selected_off_df["A_Pris"], errors="coerce").fillna(0)
            selected_off_df["Totalt"] = (selected_off_df["Antal_num"] * selected_off_df["A_Pris_num"]).astype(str)

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
                "Datum": st.column_config.TextColumn("Utförandedatum", required=True),
                "Skapad_Datum": st.column_config.TextColumn("Skapad i systemet", disabled=True),
                "Kund_Namn": st.column_config.TextColumn("Kundnamn", required=True),
                "Artikelnr": st.column_config.TextColumn("Artikelnr"),
                "Artikel": st.column_config.TextColumn("Artikel"),
                "Beskrivning": st.column_config.TextColumn("Beskrivning"),
                "Timmar": st.column_config.NumberColumn("Timmar/Antal", step=1, format="%d"),
                "Timpris": st.column_config.TextColumn("A-pris"),
                "Totalt": st.column_config.TextColumn("Totalt (kr)"),
            },
            key="editor_registrerade_poster"
        )

        edited_data["Timmar_num"] = pd.to_numeric(edited_data["Timmar"], errors="coerce").fillna(0)
        edited_data["Timpris_num"] = pd.to_numeric(edited_data["Timpris"], errors="coerce").fillna(0)
        edited_data["Totalt"] = (edited_data["Timmar_num"] * edited_data["Timpris_num"]).astype(str)
        edited_data = edited_data.drop(columns=["Timmar_num", "Timpris_num"], errors="ignore")

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
        if "Skapad_Datum" not in df_pdf.columns:
            df_pdf["Skapad_Datum"] = df_pdf["Datum"]

        df_pdf["Kund_Namn_Clean"] = df_pdf["Kund_Namn"].str.strip()
        df_pdf_valid = df_pdf[df_pdf["Kund_Namn_Clean"] != ""].copy()

        if df_pdf_valid.empty:
            st.warning("Hittade inga kunder i databasen.")
        else:
            kund_summary = (
                df_pdf_valid.groupby("Kund_Namn_Clean")
                .agg(
                    Senaste_Skapad=("Skapad_Datum", "max"),
                    Max_ID=("ID", lambda x: pd.to_numeric(x, errors="coerce").max())
                )
                .reset_index()
            )

            kund_summary = kund_summary.sort_values(
                by=["Senaste_Skapad", "Max_ID"], ascending=[False, False]
            )

            options_map = {}
            for _, row in kund_summary.iterrows():
                k_name = row["Kund_Namn_Clean"]
                d_str = row["Senaste_Skapad"]
                label = f"{k_name} ({d_str})" if d_str else k_name
                options_map[label] = k_name

            selected_label = st.radio(
                "Välj kund för fakturaunderlag:",
                options=list(options_map.keys()),
                key="radio_kund_pdf"
            )

            val_kund = options_map[selected_label]
            kund_df = df_pdf_valid[df_pdf_valid["Kund_Namn_Clean"] == val_kund]

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
# ------------------------------------------
# FLIK 6: ADMIN & ANVÄNDARHANTERING (ENDAST ADMIN)
# ------------------------------------------
if st.session_state.user_role == "admin":
  with tabs[5]:
    st.header("🔐 Admin - Hantera Användare & Lösenord")
    df_users = load_users()

    col_adm1, col_adm2 = st.columns(2)

    with col_adm1:
      st.subheader("🔑 Återställ Lösenord")
      all_users = df_users["Anvandarnamn"].tolist()
      selected_user = st.selectbox("Välj användare:", options=all_users)
      new_pass = st.text_input("Nytt lösenord", type="password", key="admin_reset_pass")

      if st.button("Spara nytt lösenord", type="primary"):
        if new_pass.strip():
          df_users.loc[df_users["Anvandarnamn"] == selected_user, "Losenord_Hash"] = hash_password(new_pass.strip())
          save_users(df_users)
          st.success(f"Lösenordet för '{selected_user}' har uppdaterats!")
        else:
          st.warning("Ange ett giltigt lösenord.")

    with col_adm2:
      st.subheader("➕ Skapa ny användare")
      new_username = st.text_input("Användarnamn", key="admin_new_user")
      new_user_pass = st.text_input("Lösenord", type="password", key="admin_new_pass")
      new_role = st.selectbox("Roll", options=["anvandare", "admin"])

      if st.button("Skapa användare"):
        if new_username.strip() and new_user_pass.strip():
          if not df_users[df_users["Anvandarnamn"].str.lower() == new_username.strip().lower()].empty:
            st.error("Användarnamnet finns redan!")
          else:
            ny_anvandare = pd.DataFrame([{
                "Anvandarnamn": new_username.strip(),
                "Losenord_Hash": hash_password(new_user_pass.strip()),
                "Roll": new_role,
            }])
            df_users = pd.concat([df_users, ny_anvandare], ignore_index=True)
            save_users(df_users)
            st.success(f"Användaren '{new_username}' har skapats!")
            st.rerun()
        else:
          st.warning("Fyll i både användarnamn och lösenord.")

    st.divider()

    st.subheader("📋 Registrerade Användare")
    st.dataframe(df_users[["Anvandarnamn", "Roll"]], use_container_width=True)

    other_users = [u for u in all_users if u != st.session_state.username]
    if other_users:
      user_to_delete = st.selectbox("Välj användare att ta bort:", options=other_users)
      if st.button("❌ Ta bort användare"):
        df_users = df_users[df_users["Anvandarnamn"] != user_to_delete].reset_index(drop=True)
        save_users(df_users)
        st.success(f"Användaren '{user_to_delete}' har tagits bort.")
        st.rerun()
