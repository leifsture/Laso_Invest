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
    "Arbetsbeskrivning",
    "Timmar",
    "Timpris",
    "Materialkostnad",
    "Ovrigt",
    "Totalt_Exkl_Moms",
    "Moms_25",
    "Totalt_Inkl_Moms",
    "Kund",
]

ARTIKEL_COLUMNS = ["Artikelnummer", "Artikelnamn", "Enhet", "A_Pris_Exkl_Moms"]

OFFERT_COLUMNS = [
    "Offertnummer",
    "Datum",
    "Kund",
    "Beskrivning",
    "Totalt_Exkl_Moms",
    "Moms_25",
    "Totalt_Inkl_Moms",
    "Status",
]

USER_COLUMNS = ["Anvandarnamn", "Losenord_Hash", "Roll"]


# ==========================================
# HELPER FUNCTIONS - SECURITY & USERS
# ==========================================
def hash_password(password: str) -> str:
  """Hashes the password using SHA-256."""
  return hashlib.sha256(password.encode()).hexdigest()


def load_users() -> pd.DataFrame:
  """Loads users from CSV. Creates default admin if file missing."""
  if os.path.exists(USER_FILE):
    try:
      df = pd.read_csv(USER_FILE, dtype=str).fillna("")
      for col in USER_COLUMNS:
        if col not in df.columns:
          df[col] = ""
      return df[USER_COLUMNS]
    except Exception:
      pass

  # Default admin account on first run
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

# Initialize Session State for Login
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

  st.stop()  # Stoppar vidare exekvering tills man är inloggad

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

# Lägg till Admin-flik om användaren har admin-roll
if st.session_state.user_role == "admin":
  tab_names.append("🔐 Admin & Användare")

tabs = st.tabs(tab_names)

# Load shared dataframes
df_arbeid = load_data(DATA_FILE, DATA_COLUMNS)
df_artiklar = load_data(ARTIKEL_FILE, ARTIKEL_COLUMNS)
df_offerter = load_data(OFFERT_FILE, OFFERT_COLUMNS)

# ------------------------------------------
# FLIK 0: REGISTRERA ARBETE
# ------------------------------------------
with tabs[0]:
  st.header("➕ Registrera utfört arbete & material")

  with st.form("registrerings_form", clear_on_submit=True):
    col1, col2 = st.columns(2)

    with col1:
      valth_datum = st.date_input("Datum", date.today())
      kund_namn = st.text_input("Kundnamn / Projekt")
      arbets_beskrivning = st.text_area("Arbetsbeskrivning")

    with col2:
      timmar = st.number_input("Antal timmar", min_value=0.0, step=0.5)
      timpris = st.number_input(
          "Timpris (exkl. moms)", min_value=0.0, value=500.0, step=50.0
      )
      material_kostnad = st.number_input(
          "Materialkostnad (exkl. moms)", min_value=0.0, step=100.0
      )
      ovrigt_kostnad = st.number_input(
          "Övriga kostnader (exkl. moms)", min_value=0.0, step=50.0
      )

    submitted = st.form_submit_button("Spara registrering", type="primary")

    if submitted:
      totalt_exkl = (timmar * timpris) + material_kostnad + ovrigt_kostnad
      moms = totalt_exkl * 0.25
      totalt_inkl = totalt_exkl + moms

      ny_rad = pd.DataFrame([{
          "Datum": str(valth_datum),
          "Arbetsbeskrivning": arbets_beskrivning,
          "Timmar": timmar,
          "Timpris": timpris,
          "Materialkostnad": material_kostnad,
          "Ovrigt": ovrigt_kostnad,
          "Totalt_Exkl_Moms": totalt_exkl,
          "Moms_25": moms,
          "Totalt_Inkl_Moms": totalt_inkl,
          "Kund": kund_namn,
      }])

      df_arbeid = pd.concat([df_arbeid, ny_rad], ignore_index=True)
      save_data(df_arbeid, DATA_FILE)
      st.success("Registreringen har sparats!")
      st.rerun()

# ------------------------------------------
# FLIK 1: OFFERTER
# ------------------------------------------
with tabs[1]:
  st.header("📑 Offertförfrågningar & Skapa offerter")

  with st.form("offert_form", clear_on_submit=True):
    col_o1, col_o2 = st.columns(2)
    with col_o1:
      offert_kund = st.text_input("Kund / Företag")
      offert_beskrivning = st.text_area("Offertbeskrivning / Omfattning")
    with col_o2:
      offert_summa_exkl = st.number_input(
          "Beräknat belopp (exkl. moms)", min_value=0.0, step=500.0
      )
      offert_status = st.selectbox(
          "Status", ["Skapad", "Skickad", "Accepterad", "Avslagen"]
      )

    submit_offert = st.form_submit_button("Skapa offert")

    if submit_offert:
      offert_nr = f"OFF-{len(df_offerter) + 1001}"
      moms = offert_summa_exkl * 0.25
      totalt_inkl = offert_summa_exkl + moms

      ny_offert = pd.DataFrame([{
          "Offertnummer": offert_nr,
          "Datum": str(date.today()),
          "Kund": offert_kund,
          "Beskrivning": offert_beskrivning,
          "Totalt_Exkl_Moms": offert_summa_exkl,
          "Moms_25": moms,
          "Totalt_Inkl_Moms": totalt_inkl,
          "Status": offert_status,
      }])

      df_offerter = pd.concat([df_offerter, ny_offert], ignore_index=True)
      save_data(df_offerter, OFFERT_FILE)
      st.success(f"Offert {offert_nr} har skapats!")
      st.rerun()

  st.subheader("📋 Befintliga offerter")
  st.dataframe(df_offerter, use_container_width=True)

# ------------------------------------------
# FLIK 2: ARTIKELDATABAS
# ------------------------------------------
with tabs[2]:
  st.header("📦 Artikel- & Prisdatabas")

  with st.form("artikel_form", clear_on_submit=True):
    col_art1, col_art2 = st.columns(2)
    with col_art1:
      art_nr = st.text_input("Artikelnummer")
      art_namn = st.text_input("Artikelnamn")
    with col_art2:
      art_enhet = st.selectbox("Enhet", ["st", "timmar", "m", "m2", "kg", "l"])
      art_pris = st.number_input("A-pris exkl. moms", min_value=0.0, step=10.0)

    submit_art = st.form_submit_button("Spara artikel")

    if submit_art:
      ny_art = pd.DataFrame([{
          "Artikelnummer": art_nr,
          "Artikelnamn": art_namn,
          "Enhet": art_enhet,
          "A_Pris_Exkl_Moms": art_pris,
      }])

      df_artiklar = pd.concat([df_artiklar, ny_art], ignore_index=True)
      save_data(df_artiklar, ARTIKEL_FILE)
      st.success("Artikeln har lagts till!")
      st.rerun()

  st.subheader("📋 Artikellista")
  st.dataframe(df_artiklar, use_container_width=True)

# ------------------------------------------
# FLIK 3: REDIGERA / TA BORT
# ------------------------------------------
with tabs[3]:
  st.header("✏️ Hantera och redigera registrerad data")

  if not df_arbeid.empty:
    st.dataframe(df_arbeid, use_container_width=True)

    rad_index = st.number_input(
        "Välj radindex att ta bort",
        min_value=0,
        max_value=len(df_arbeid) - 1,
        step=1,
    )
    if st.button("❌ Ta bort vald rad", type="secondary"):
      df_arbeid = df_arbeid.drop(index=rad_index).reset_index(drop=True)
      save_data(df_arbeid, DATA_FILE)
      st.success("Raden har tagits bort!")
      st.rerun()
  else:
    st.info("Inga registreringar finns ännu.")

# ------------------------------------------
# FLIK 4: FAKTURAUNDERLAG
# ------------------------------------------
with tabs[4]:
  st.header("📄 Skapa fakturaunderlag")

  if not df_arbeid.empty:
    kunder = list(df_arbeid["Kund"].unique())
    valdh_kund = st.selectbox("Välj kund för sammanställning", kunder)

    kund_df = df_arbeid[df_arbeid["Kund"] == valdh_kund]

    st.subheader(f"Underlag för: {valdh_kund}")
    st.dataframe(kund_df, use_container_width=True)

    tot_exkl = kund_df["Totalt_Exkl_Moms"].sum()
    tot_moms = kund_df["Moms_25"].sum()
    tot_inkl = kund_df["Totalt_Inkl_Moms"].sum()

    m_col1, m_col2, m_col3 = st.columns(3)
    m_col1.metric("Totalt exkl. moms", f"{tot_exkl:,.2f} kr")
    m_col2.metric("Moms (25%)", f"{tot_moms:,.2f} kr")
    m_col3.metric("Totalt inkl. moms", f"{tot_inkl:,.2f} kr")
  else:
    st.info("Det finns inget underlag att visa.")

# ------------------------------------------
# FLIK 5: ADMIN & ANVÄNDARHANTERING (ENDAST ADMIN)
# ------------------------------------------
if st.session_state.user_role == "admin":
  with tabs[5]:
    st.header("🔐 Admin - Hantera Användare & Lösenord")
    df_users = load_users()

    col_adm1, col_adm2 = st.columns(2)

    # 1. Återställ lösenord
    with col_adm1:
      st.subheader("🔑 Återställ Lösenord")
      all_users = df_users["Anvandarnamn"].tolist()
      selected_user = st.selectbox("Välj användare:", options=all_users)
      new_pass = st.text_input(
          "Nytt lösenord", type="password", key="admin_reset_pass"
      )

      if st.button("Spara nytt lösenord", type="primary"):
        if new_pass.strip():
          df_users.loc[
              df_users["Anvandarnamn"] == selected_user, "Losenord_Hash"
          ] = hash_password(new_pass.strip())
          save_users(df_users)
          st.success(f"Lösenordet för '{selected_user}' har uppdaterats!")
        else:
          st.warning("Ange ett giltigt lösenord.")

    # 2. Skapa ny användare
    with col_adm2:
      st.subheader("➕ Skapa ny användare")
      new_username = st.text_input("Användarnamn", key="admin_new_user")
      new_user_pass = st.text_input(
          "Lösenord", type="password", key="admin_new_pass"
      )
      new_role = st.selectbox(
          "Roll",
          options=["anvandare", "admin"],
          help="Vanliga användare ser inte denna Admin-flik.",
      )

      if st.button("Skapa användare"):
        if new_username.strip() and new_user_pass.strip():
          if not df_users[
              df_users["Anvandarnamn"].str.lower()
              == new_username.strip().lower()
          ].empty:
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

    # 3. Lista alla användare och radera
    st.subheader("📋 Registrerade Användare")
    st.dataframe(
        df_users[["Anvandarnamn", "Roll"]], use_container_width=True
    )

    user_to_delete = st.selectbox(
        "Välj användare att ta bort:",
        options=[u for u in all_users if u != st.session_state.username],
    )
    if st.button("❌ Ta bort användare"):
      df_users = df_users[
          df_users["Anvandarnamn"] != user_to_delete
      ].reset_index(drop=True)
      save_users(df_users)
      st.success(f"Användaren '{user_to_delete}' har tagits bort.")
      st.rerun()
