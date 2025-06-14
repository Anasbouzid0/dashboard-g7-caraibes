# pages/Suivi_Technicien.py
import streamlit as st
import pandas as pd
import altair as alt
from io import BytesIO

st.set_page_config(page_title="Suivi détaillé par technicien", layout="centered")

# === CHARGEMENT DES DONNÉES ===
df = pd.read_excel("Canal inter.xlsx", sheet_name="SUIVI JOURNALIER CANAL")

# Renommer les colonnes si nécessaire
if 'Nom technicien' in df.columns:
    df.rename(columns={"Nom technicien": "NOM"}, inplace=True)

# === SUIVI DYNAMIQUE DES INTERVENTIONS ===
st.title("Suivi des interventions")

# Liste des techniciens + "Tous" en premier
techniciens = sorted(df["NOM"].dropna().unique().tolist())
techniciens.insert(0, "Tous")

# Sélecteur
technicien_choisi = st.selectbox("Choisir un technicien", techniciens)

# Filtrage dynamique
df_filtered = df.copy() if technicien_choisi == "Tous" else df[df["NOM"] == technicien_choisi]

# Calculs dynamiques
total_planifies = df_filtered['OT planifiés'].sum()
ot_real = df_filtered['OT Réalisé'].sum()
ot_ok = df_filtered['OT OK'].sum()
ot_nok = df_filtered['OT NOK'].sum()
ot_report = df_filtered['OT Reportes'].sum()

# Affichage KPI
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
kpi1.metric("OT Planifiés", int(total_planifies))
kpi2.metric("OT Réalisés", int(ot_real))
kpi3.metric("OT OK / NOK", f"{int(ot_ok)} / {int(ot_nok)}")
kpi4.metric("OT Reportés", int(ot_report))

# === GRAPHIQUE : OT Réalisés par jour ===
if 'Date' in df_filtered.columns and 'OT Réalisé' in df_filtered.columns:
    df_filtered['Date'] = pd.to_datetime(df_filtered['Date'], errors='coerce')
    montant_par_jour = df_filtered.groupby('Date')['OT Réalisé'].sum().reset_index()
    montant_par_jour['Jour'] = montant_par_jour['Date'].dt.strftime('%d')

    st.subheader("OT Réalisés par jour")
    chart = alt.Chart(montant_par_jour).mark_line(point=True).encode(
        x=alt.X('Jour:O', title='Mai', sort=montant_par_jour['Jour'].tolist()),
        y=alt.Y('OT Réalisé:Q', title='OT Réalisé'),
        tooltip=['Jour', 'OT Réalisé']
    ).properties(height=400)

    st.altair_chart(chart, use_container_width=True)

# === TABLEAU INTERACTIF FILTRÉ ===
st.subheader("Suivi JOURNALIER CANAL D3")
colonnes_affichees = ["Date", "NOM", "État", "OT planifiés", "OT Réalisé", "OT OK", "OT NOK", "OT Reportes"]
df_affiche = df_filtered[colonnes_affichees]

with st.expander("Afficher le tableau des interventions"):
    st.dataframe(df_affiche, use_container_width=True)

# === EXPORT EXCEL ===
def convertir_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Interventions")
    return output.getvalue()

nom_fichier = "Interventions_Tous.xlsx" if technicien_choisi == "Tous" else f"Interventions_{technicien_choisi.replace(' ', '_')}.xlsx"
fichier_excel = convertir_excel(df_affiche)

st.download_button(
    label="Télécharger Excel",
    data=fichier_excel,
    file_name=nom_fichier,
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# === TAUX CALCULÉS DYNAMIQUEMENT ===
st.subheader("Taux de performance (%)")

def safe_div(numerator, denominator):
    return (numerator / denominator * 100) if denominator != 0 else 0.0

taux_reussite = safe_div(ot_ok, ot_real)
taux_echec = safe_div(ot_nok, ot_real)
taux_report = safe_div(ot_report, total_planifies)
taux_cloture = safe_div(ot_real, total_planifies)

col1, col2, col3, col4 = st.columns(4)
col1.metric("% Réussite (OK)", f"{taux_reussite:.2f}%")
col2.metric("% Échec (NOK)", f"{taux_echec:.2f}%")
col3.metric("% Reportés", f"{taux_report:.2f}%")
col4.metric("% Clôturés", f"{taux_cloture:.2f}%")
