from pathlib import Path

import pandas as pd
import streamlit as st

DOSSIER = Path(__file__).parent / "donnees"

st.set_page_config(page_title="L'électricité dans 12 quartiers", page_icon="⚡")

st.title("L'électricité dans 12 quartiers")
st.caption("Relevés mensuels de janvier 2024 à décembre 2025. Données fictives.")


@st.cache_data
def charger():
    return pd.read_csv(DOSSIER / "consommation_propre.csv")


df = charger()

st.write("Question du directeur : la consommation suit-elle la chaleur, ou les heures de courant ?")
st.write("Relevés de 12 quartiers de Port-au-Prince, Delmas, Pétion-Ville et Cap-Haïtien.")

# Filtres
communes = sorted(df["commune"].unique())
choix_communes = st.sidebar.multiselect("Communes", communes, default=communes)
annees = sorted(df["annee"].unique())
choix_annee = st.sidebar.selectbox("Année", annees, index=annees.index(2025))

if not choix_communes:
    st.warning("Choisissez au moins une commune.")
    st.stop()

filtre = df[(df["commune"].isin(choix_communes)) & (df["annee"] == choix_annee)]
toutes_annees = df[df["commune"].isin(choix_communes)]

# Indicateurs
c1, c2, c3 = st.columns(3)
c1.metric("Consommation totale", f"{filtre['kwh'].sum() / 1e6:.2f} millions de kWh")
c2.metric("Par abonné", f"{filtre['kwh_par_abonne'].mean():.1f} kWh")
c3.metric("Heures de courant", f"{filtre['heures_courant'].mean():.1f} h")

# Onglets
t4, t5, t6, t7, t8 = st.tabs(
    ["Quartiers", "Évolution", "Chaleur ou courant ?", "Coupures", "Relevés hors norme"]
)

with t4:
    par_quartier = filtre.groupby("quartier")["kwh_par_abonne"].mean().sort_values()
    st.bar_chart(par_quartier)
    st.write(f"{par_quartier.idxmax()} consomme le plus par abonné ({par_quartier.max():.1f} kWh par mois).")

with t5:
    courbes = toutes_annees.groupby(["mois", "commune"])["kwh_par_abonne"].mean().unstack()
    st.line_chart(courbes)
    totaux = toutes_annees.pivot_table(index="commune", columns="annee", values="kwh", aggfunc="sum")
    if {2024, 2025}.issubset(totaux.columns):
        hausse = (totaux[2025] / totaux[2024] - 1) * 100
        st.write(f"{hausse.idxmax()} progresse le plus : {hausse.max():+.1f} % entre 2024 et 2025.")
with t6:
    res = toutes_annees[toutes_annees["type"] == "Résidentiel"]
    if len(res) > 2:
        corr_courant = res["kwh_par_abonne"].corr(res["heures_courant"])
        corr_chaleur = res["kwh_par_abonne"].corr(res["temperature_c"])
        ...
        st.scatter_chart(res, x="heures_courant", y="kwh_par_abonne")
        st.scatter_chart(res, x="temperature_c", y="kwh_par_abonne")
        st.write(f"Corrélation avec les heures de courant : {corr_courant:.2f} ; avec la température : {corr_chaleur:.2f}.")
    else:
        st.write("Pas assez de relevés résidentiels pour cette sélection.")

with t7:
    st.bar_chart(filtre.groupby("commune")["heures_courant"].median())
    courts = filtre[filtre["heures_courant"] < 8]
    st.write(f"{len(courts)} relevé(s) sous 8 heures de courant par jour.")
    if len(courts):
        st.dataframe(courts[["mois", "quartier", "commune", "heures_courant"]])

with t8:
    top = filtre.nlargest(3, "kwh")[["mois", "quartier", "type", "kwh"]]
    st.dataframe(top)

# Conclusion
st.markdown(
    "### Conclusion\n"
    "La consommation par abonné suit les heures de courant (corrélation 0,76) "
    "bien plus que la chaleur (-0,15). Une corrélation ne prouve pas une cause."
)

with st.expander("Voir les données filtrées"):
    st.dataframe(filtre)