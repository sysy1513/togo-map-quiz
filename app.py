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

# --- 1. CONFIGURATION MOBILE & DESIGN ---
st.set_page_config(page_title="Togo Map Quiz - JCDC TOGO", layout="wide")
st.markdown(
    """
    <style>
        .stTabs [data-baseweb="tab-list"] { gap: 10px; }
        .stTabs [data-baseweb="tab"] { height: 50px; background-color: #f0f2f6; border-radius: 10px 10px 0 0; font-weight: bold; }
    </style>
    """, 
    unsafe_allow_html=True
)

def normaliser(texte):
    return unidecode(str(texte)).strip().lower()

@st.cache_data
def charger_donnees(path, niveau):
    data = gpd.read_file(path)
    col = 'ADM2_FR' if niveau == "Préfectures" else 'Communes'
    data = data.dropna(subset=[col])
    return data, data.to_crs(epsg=4326), col

# --- 2. INITIALISATION DES ÉTATS ---
if 'score' not in st.session_state: st.session_state.score = 0
if 'nb_q' not in st.session_state: st.session_state.nb_q = 0
if 'cible' not in st.session_state: st.session_state.cible = None
if 'termine' not in st.session_state: st.session_state.termine = False
if 'start_time' not in st.session_state: st.session_state.start_time = None

# VERROU STRICT : Si une question a été posée, le mode "jeu" est activé
jeu_en_cours = st.session_state.nb_q > 0 and not st.session_state.termine

# --- 3. BARRE LATÉRALE ---
with st.sidebar:
    if os.path.exists("assets/logo_jcdc.png"):
        st.image("assets/logo_jcdc.png", width=150)
    st.title("🇹🇬 JCDC TOGO")
    st.write("Directeur : **Sylvestre BOCCO**")
    st.markdown("---")
    niveau = st.selectbox("Échelle d'analyse", ["Préfectures", "Communes"])
    path = f"data/{niveau}_Togo.shp"
    
    if st.button("🔄 Réinitialiser tout le Quiz"):
        st.session_state.score = 0
        st.session_state.nb_q = 0
        st.session_state.termine = False
        st.session_state.cible = None
        st.session_state.start_time = None
        st.rerun()

try:
    df, df_gps, col_nom = charger_donnees(path, niveau)
except:
    st.error("⚠️ Fichiers de données manquants dans le dossier /data")
    st.stop()

# --- 4. INTERFACE À ONGLETS ---
tab1, tab2, tab3, tab4 = st.tabs(["📖 RÉVISION", "🎮 DÉFI (30s)", "🏆 CLASSEMENT", "❓ INFOS"])

with tab1:
    # --- BLOCAGE PHYSIQUE DE LA RÉVISION ---
    if jeu_en_cours:
        st.error("🚫 **ACCÈS INTERDIT**")
        st.warning("Le mode Défi est lancé. Vous ne pouvez plus consulter la carte de révision.")
        st.image("https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNHJueGZ3eHByZzR3eHByZzR3eHByZzR3eHByZzR3eHByZyZlcD12MV9pbnRlcm5hbF9naWZfYnlfaWQmY3Q9Zw/3o7TKtnuHOH6y2Luz6/giphy.gif")
    else:
        st.subheader("Explorez la carte interactive avant le défi")
        fig_rev = px.choropleth_mapbox(df_gps, geojson=df_gps.geometry, locations=df_gps.index, color=col_nom, 
                                      mapbox_style="carto-positron", zoom=6, center={"lat": 8.6, "lon": 1.2}, 
                                      opacity=0.6, hover_name=col_nom)
        fig_rev.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        st.plotly_chart(fig_rev, use_container_width=True)

with tab2:
    if not st.session_state.termine:
        if st.session_state.nb_q < 5:
            # GESTION DU CHRONO 30 SECONDES
            if st.session_state.start_time is None:
                st.session_state.start_time = time.time()
            
            ecoule = time.time() - st.session_state.start_time
            restant = max(0, 30 - int(ecoule))
            
            c1, c2 = st.columns(2)
            c1.metric("Question", f"{st.session_state.nb_q + 1}/5")
            c2.metric("Temps Restant", f"{restant}s")

            if restant <= 0:
                st.error("⌛ Temps écoulé pour cette question !")
                st.session_state.nb_q += 1
                st.session_state.start_time = None
                st.session_state.cible = None
                time.sleep(2)
                st.rerun()

            if st.session_state.cible is None:
                st.session_state.cible = random.choice(df[col_nom].unique().tolist())

            fig, ax = plt.subplots(figsize=(5, 7))
            df.plot(ax=ax, color='#f0f0f0', edgecolor='#333333', linewidth=0.5)
            df[df[col_nom] == st.session_state.cible].plot(ax=ax, color='#e74c3c')
            plt.axis('off')
            st.pyplot(fig)

            with st.form(key=f"form_{st.session_state.nb_q}"):
                rep = st.text_input("Quelle est la zone en rouge ?")
                if st.form_submit_button("Valider"):
                    if normaliser(rep) == normaliser(st.session_state.cible):
                        st.success("Excellent !")
                        st.session_state.score += 1
                    else:
                        st.error(f"Faux ! C'était : {st.session_state.cible}")
                    st.session_state.nb_q += 1
                    st.session_state.cible = None
                    st.session_state.start_time = None
                    time.sleep(1)
                    st.rerun()
        else:
            st.session_state.termine = True
            st.rerun()
    else:
        st.balloons()
        st.header(f"Score : {st.session_state.score}/5")
        user_name = st.text_input("Votre nom complet pour l'attestation :")
        if user_name and st.button("🎓 Générer mon Attestation Prestige"):
            pdf = FPDF(orientation='L', unit='mm', format='A4')
            pdf.add_page()
            
            # --- DESIGN PRESTIGE ---
            # Bordure Verte (Togo)
            pdf.set_draw_color(0, 106, 77); pdf.set_line_width(3); pdf.rect(5, 5, 287, 200)
            # Bordure Jaune
            pdf.set_draw_color(255, 206, 0); pdf.set_line_width(1); pdf.rect(8, 8, 281, 194)
            
            # Logos (Drapeau à gauche, JCDC à droite)
            try:
                pdf.image("assets/drapeau_togo.png", 15, 15, 40)
                pdf.image("assets/logo_jcdc.png", 240, 15, 40)
            except: pass
            
            pdf.set_font("Arial", 'B', 35); pdf.set_text_color(0, 106, 77)
            pdf.set_y(60); pdf.cell(277, 20, "ATTESTATION DE RÉUSSITE", ln=True, align='C')
            
            pdf.set_font("Arial", '', 20); pdf.set_text_color(0, 0, 0)
            pdf.cell(277, 15, "Décernée fièrement à :", ln=True, align='C')
            
            pdf.set_font("Arial", 'B', 30); pdf.set_text_color(180, 140, 0)
            pdf.cell(277, 25, user_name.upper(), ln=True, align='C')
            
            pdf.set_font("Arial", '', 16); pdf.set_text_color(0, 0, 0)
            pdf.multi_cell(277, 10, f"Pour avoir démontré une expertise géographique exceptionnelle\nlors du Togo Map Quiz (Niveau {niveau}).", align='C')
            
            # Signature
            try: pdf.image("assets/signature.png", 120, 160, 50)
            except: pass
            
            pdf.set_y(180); pdf.set_font("Arial", 'B', 14)
            pdf.cell(277, 8, "SYLVESTRE BOCCO", ln=True, align='C')
            pdf.set_font("Arial", '', 11)
            pdf.cell(277, 5, "Directeur de JCDC TOGO", ln=True, align='C')
            
            pdf.output("attestation_jcdc.pdf")
            with open("attestation_jcdc.pdf", "rb") as f:
                st.download_button("📩 Télécharger l'Attestation", f, "Attestation_JCDC_Togo.pdf")

with tab3:
    st.subheader("🥇 Top des Experts")
    # Affichage du classement (Code précédent)

with tab4:
    st.write("Édition Spéciale MAP QUIZ TOGO. Sécurité et Chrono activés.")
