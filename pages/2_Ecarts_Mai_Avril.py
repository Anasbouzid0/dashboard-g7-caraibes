# pages/1_Ecarts_Mai_Avril.py
import streamlit as st
import pandas as pd
import altair as alt
from io import BytesIO

st.set_page_config(page_title="Suivi des Écarts de Performance", layout="centered")

# Style CSS pour compatibilité mobile et suppression des marges inutiles
st.markdown("""
    <style>
        .block-container {
            padding: 1rem 0.5rem !important;
        }
        @media screen and (max-width: 768px) {
            .block-container {
                padding: 0.5rem !important;
            }
            .css-1y0tads {
                overflow-x: scroll;
            }
        }
    </style>
""", unsafe_allow_html=True)

st.title("Analyse Comparative des Performances : Mai vs Avril")

# === Chargement des données ===
file_path = "Ecart.xlsx"
try:
    df_mai = pd.read_excel(file_path, sheet_name="SUIVI HEBDOMADAIRE MAI")
    df_avril = pd.read_excel(file_path, sheet_name="SUIVI HEBDOMADAIRE Avril")
except Exception as e:
    st.error(f"Erreur lors du chargement : {e}")
    st.stop()

# Nettoyage des colonnes
cols_to_compare = [
    "Planifiés", "Ok", "Nok", "Reportés",
    "Taux Réussite", "Taux Echec", "Taux Report", "Taux Cloture",
    "Montant prévu", "Montant réel", "Montant echec"
]

for df in [df_mai, df_avril]:
    df.columns = df.columns.str.strip()

# Extraction et alignement
mai = df_mai[["Semaine"] + cols_to_compare].set_index("Semaine")
avril = df_avril[["Semaine"] + cols_to_compare].set_index("Semaine")
avril = avril.loc[mai.index]

# Calcul des écarts MAI vs AVRIL
ecarts_avr = ((mai - avril) / avril.replace(0, pd.NA)) * 100
ecarts_avr = ecarts_avr.clip(lower=-100, upper=100).round(2)
ecarts_avr.loc["MOYENNE"] = ecarts_avr.mean()

# Moyenne générale (tout indicateur, tout confondu)
moyenne_generale = ecarts_avr.drop(index="MOYENNE").mean().mean().round(2)

# === Filtres dynamiques intégrés à la page ===
with st.container():
    st.subheader("Sélection de la Vue")
    col1, col2 = st.columns([2, 1])
    with col1:
        mode_vue = st.radio("Comparer :", ["Vue Globale (Moyenne)", "Vue par Semaine"], horizontal=True)
    with col2:
        st.metric(label="Moyenne Générale des Écarts Mai/Avril", value=f"{moyenne_generale}%")

# === Affichage Tableau (remplacé AgGrid par dataframe pour compatibilité mobile) ===
st.markdown("### Synthèse des Écarts - Mois de Mai comparé à Avril")
with st.expander("Afficher le tableau des écarts"):
    st.dataframe(ecarts_avr.reset_index(), use_container_width=True)

# === Graphiques dynamiques avec barres d'évolution ===
def afficher_graphique(df, indicateurs, titre):
    df_no_avg = df.drop(index="MOYENNE")
    long_df = df_no_avg[indicateurs].reset_index().melt(id_vars="Semaine", var_name="Indicateur", value_name="Écart (%)")
    moyenne = df.loc["MOYENNE", indicateurs].reset_index()
    moyenne.columns = ["Indicateur", "Écart (%)"]

    if mode_vue == "Vue Globale (Moyenne)":
        chart = alt.Chart(moyenne).mark_bar(size=40).encode(
            x=alt.X("Indicateur:N", title=f"% Écart — {titre}"),
            y=alt.Y("Écart (%):Q", scale=alt.Scale(domain=[-100, 100])),
            color=alt.condition("datum['Écart (%)'] > 0", alt.value("green"), alt.value("red")),
            tooltip=["Indicateur", "Écart (%)"]
        ).properties(height=300, title=f"Variation Moyenne - {titre}")
        st.altair_chart(chart, use_container_width=True)

    else:
        ligne = alt.Chart(long_df).mark_line(point=True).encode(
            x=alt.X("Semaine:N", title="Semaine"),
            y=alt.Y("Écart (%):Q", scale=alt.Scale(domain=[-100, 100])),
            color=alt.Color("Indicateur:N", legend=alt.Legend(title=f"% Écart — {titre}")),
            tooltip=["Semaine", "Indicateur", "Écart (%)"]
        ).properties(height=400, title=f"Évolution Hebdomadaire - {titre}")

        st.altair_chart(ligne, use_container_width=True)

# === Affichage des sections ===
st.markdown("### Indicateurs d’Activité : OK / NOK / Reportés")
action_cols = ["Ok", "Nok", "Reportés"]
afficher_graphique(ecarts_avr, action_cols, "Activité (Mai/Avril)")

st.markdown("### Indicateurs Financiers : Montants")
labels_abbr = {"Montant prévu": "M. Prévu", "Montant réel": "M. Réel", "Montant echec": "M. Échec"}
ecarts_avr = ecarts_avr.rename(columns=labels_abbr)
montant_abbr_cols = list(labels_abbr.values())
afficher_graphique(ecarts_avr, montant_abbr_cols, "Financier (Mai/Avril)")

st.markdown("### Indicateurs de Performance : Taux")
taux_cols = ["Taux Réussite", "Taux Echec", "Taux Report", "Taux Cloture"]
afficher_graphique(ecarts_avr, taux_cols, "Taux de Performance (Mai/Avril)")

# === Export ===
buffer = BytesIO()
with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
    ecarts_avr.to_excel(writer, sheet_name="Écarts Mai-Avril")
st.download_button("Télécharger les Données (Excel)", buffer.getvalue(), file_name="ecarts_mai_avril.xlsx")
