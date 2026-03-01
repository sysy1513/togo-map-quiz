import streamlit as st
import geopandas as gpd
import matplotlib.pyplot as plt
import plotly.express as px
import pandas as pd
import random
import time
import os
from fpdf import FPDF
from unidecode import unidecode
from PIL import Image

# --- CONFIGURATION ---
st.set_page_config(page_title="Togo Map Quiz - JCDC TOGO", layout="wide")

def normaliser(texte):
    return unidecode(str(texte)).strip().lower()

@st.cache_data
def charger_donnees(path, niveau):
    data = gpd.read_file(path)
    col = 'ADM2_FR' if niveau == "Préfectures" else 'Communes'
    data = data.dropna(subset=[col])
    data_gps = data.to_crs(epsg=4326)
    return data, data_gps, col

def sauvegarder_score(nom, score, niveau):
    fichier = "leaderboard.csv"
    nouveau = pd.DataFrame([[nom, score, niveau, time.strftime('%d/%m/%Y')]], 
                            columns=["Nom", "Score", "Niveau", "Date"])
    if os.path.exists(fichier):
        df_l = pd.read_csv(fichier)
        df_l = pd.concat([df_l, nouveau], ignore_index=True)
    else:
        df_l = nouveau
    df_l.to_csv(fichier, index=False)

# --- INITIALISATION ---
if 'score' not in st.session_state: st.session_state.score = 0
if 'nb_q' not in st.session_state: st.session_state.nb_q = 0
if 'cible' not in st.session_state: st.session_state.cible = None
if 'termine' not in st.session_state: st.session_state.termine = False

# --- SIDEBAR BRANDING ---
with st.sidebar:
    try: 
        st.image("assets/logo_jcdc.png", width=150)
    except: 
        st.write("📌 **JCDC TOGO**")
    
    st.title("Direction Générale")
    st.write("Responsable : **Sylvestre BOCCO**")
    
    try: 
        st.image("assets/drapeau_togo.png", width=80)
    except: 
        st.write("🇹🇬 Togo")
    
    st.markdown("---")
    niveau = st.selectbox("Échelle de jeu", ["Préfectures", "Communes"])
    path = f"data/{niveau}_Togo.shp"
    
    if st.button("🔄 Réinitialiser le Quiz"):
        for k in ["score", "nb_q", "termine"]: 
            st.session_state[k] = 0 if k != "termine" else False
        st.session_state.cible = None
        st.rerun()

# Chargement sécurisé
try:
    df, df_gps, col_nom = charger_donnees(path, niveau)
except Exception as e:
    st.error(f"Erreur de données : {e}")
    st.stop()

# --- INTERFACE ---
tab1, tab2, tab3, tab4 = st.tabs(["📖 Révision", "🎮 Défi", "🏆 Classement", "❓ Guide"])

with tab1:
    st.subheader("Explorez la carte interactive")
    fig_rev = px.choropleth_mapbox(df_gps, geojson=df_gps.geometry, locations=df_gps.index, color=col_nom, mapbox_style="carto-positron", zoom=6, center={"lat": 8.6, "lon": 1.2}, opacity=0.5, hover_name=col_nom)
    fig_rev.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    st.plotly_chart(fig_rev, use_container_width=True)

with tab2:
    if not st.session_state.termine:
        if st.session_state.nb_q < 5:
            st.info(f"Question {st.session_state.nb_q + 1}/5 | Score : {st.session_state.score}")
            if st.session_state.cible is None: 
                st.session_state.cible = random.choice(df[col_nom].unique().tolist())
            
            fig, ax = plt.subplots(figsize=(6, 8))
            df.plot(ax=ax, color='whitesmoke', edgecolor='black', linewidth=0.5)
            df[df[col_nom] == st.session_state.cible].plot(ax=ax, color='red')
            plt.axis('off'); st.pyplot(fig)

            with st.form(key=f"f_{st.session_state.nb_q}"):
                rep = st.text_input("Quelle est la zone en rouge ?")
                if st.form_submit_button("Valider ✅"):
                    if normaliser(rep) == normaliser(st.session_state.cible):
                        st.success("Correct !"); st.session_state.score += 1
                    else: 
                        st.error(f"Faux... C'était {st.session_state.cible}")
                    st.session_state.nb_q += 1; st.session_state.cible = None; time.sleep(1); st.rerun()
        else: 
            st.session_state.termine = True; st.rerun()
    else:
        st.balloons(); st.header(f"Score Final : {st.session_state.score}/5")
        nom_c = st.text_input("Saisissez votre nom complet :")
        if nom_c:
            c1, c2 = st.columns(2)
            with c1:
                if st.button("🏆 Enregistrer mon Score"):
                    sauvegarder_score(nom_c, st.session_state.score, niveau); st.success("Score enregistré !")
            with c2:
                if st.button("🎓 Générer mon Certificat"):
                    pdf = FPDF(orientation='L', unit='mm', format='A4'); pdf.add_page()
                    pdf.set_draw_color(0, 106, 77); pdf.set_line_width(2); pdf.rect(5, 5, 287, 200)
                    pdf.set_draw_color(255, 206, 0); pdf.set_line_width(1); pdf.rect(10, 10, 277, 190)
                    try: 
                        pdf.image("assets/logo_jcdc.png", 20, 20, 35)
                        pdf.image("assets/drapeau_togo.png", 240, 20, 35)
                    except: pass
                    
                    pdf.set_y(65); pdf.set_font("Arial", 'B', 35); pdf.set_text_color(0, 106, 77)
                    pdf.cell(277, 20, "CERTIFICAT DE REUSSITE", ln=True, align='C')
                    pdf.ln(10); pdf.set_font("Arial", 'I', 20); pdf.set_text_color(0, 0, 0)
                    pdf.cell(277, 10, "Decerne a :", ln=True, align='C')
                    pdf.ln(5); pdf.set_font("Arial", 'B', 30); pdf.set_text_color(216, 12, 18)
                    pdf.cell(277, 20, nom_c.upper(), ln=True, align='C')
                    
                    # SIGNATURE DIRECTEUR (FIXE)
                    pdf.set_y(160); pdf.set_font("Arial", 'B', 14); pdf.set_text_color(0, 0, 0)
                    pdf.cell(277, 10, f"Fait le {time.strftime('%d/%m/%Y')} | JCDC TOGO", ln=True, align='C')
                    pdf.set_font("Arial", 'B', 16); pdf.set_text_color(0, 106, 77)
                    pdf.cell(277, 10, "SYLVESTRE BOCCO", ln=True, align='C')
                    pdf.set_font("Arial", '', 12); pdf.set_text_color(0, 0, 0)
                    pdf.cell(277, 10, "Directeur de JCDC TOGO", ln=True, align='C')
                    
                    pdf.output("certif.pdf")
                    with open("certif.pdf", "rb") as f: 
                        st.download_button("⬇️ Télécharger le PDF", f, f"Certificat_{nom_c}.pdf")

with tab3:
    st.subheader("🥇 Top 10 des Experts")
    if os.path.exists("leaderboard.csv"):
        st.table(pd.read_csv("leaderboard.csv").sort_values(by="Score", ascending=False).head(10))
    else: 
        st.info("Aucun score enregistré.")

with tab4:
    st.header("📖 Guide de l'Utilisateur")
    st.write("""
    1. **Révision** : Explorez la carte avec le zoom pour apprendre les noms.
    2. **Défi** : Identifiez la zone rouge. Le score s'affiche en temps réel.
    3. **Classement** : Enregistrez votre score pour entrer dans l'histoire.
    4. **Certificat** : Téléchargez votre titre officiel signé par le Directeur.
    """)