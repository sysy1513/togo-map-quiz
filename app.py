import streamlit as st
import geopandas as gpd
import plotly.express as px
import random
import time
import os
from fpdf import FPDF
from unidecode import unidecode
from PIL import Image

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Togo Map Quiz - Sylvestre BOCCO (JCDC TOGO)", layout="wide")

def normaliser(texte):
    return unidecode(str(texte)).strip().lower()

@st.cache_data
def charger_donnees(chemin, type_jeu):
    data = gpd.read_file(chemin)
    col_nom = 'ADM2_FR' if type_jeu == "Préfectures" else 'Communes'
    data = data.dropna(subset=[col_nom])
    # Conversion en WGS84 pour l'interactivité Plotly (Zoom)
    data = data.to_crs(epsg=4326)
    return data, col_nom

# --- INITIALISATION ---
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'nb_questions' not in st.session_state:
    st.session_state.nb_questions = 0
if 'termine' not in st.session_state:
    st.session_state.termine = False
if 'cible' not in st.session_state:
    st.session_state.cible = None

# --- BARRE LATÉRALE (BRANDING JCDC) ---
with st.sidebar:
    try:
        logo = Image.open("assets/logo_jcdc.png")
        st.image(logo, width=180)
    except:
        st.info("Logo JCDC")
    
    st.title("JCDC TOGO")
    st.subheader("Direction : Sylvestre BOCCO")
    
    try:
        drapeau = Image.open("assets/drapeau_togo.png")
        st.image(drapeau, width=80)
    except:
        st.info("🇹🇬 Togo")
    
    st.markdown("---")
    niveau = st.selectbox("Choisir le niveau", ["Préfectures", "Communes"])
    path = "data/Prefectures_Togo.shp" if niveau == "Préfectures" else "data/Communes_Togo.shp"
    
    if st.button("🔄 Réinitialiser le Quiz"):
        st.session_state.score = 0
        st.session_state.nb_questions = 0
        st.session_state.termine = False
        st.rerun()

df, col_nom = charger_donnees(path, niveau)

# --- CORPS DE L'APPLICATION ---
st.title("🌍 Togo Map Quiz Interactif")
tab1, tab2 = st.tabs(["📖 Révision & Exploration", "🎮 Le Défi"])

with tab1:
    st.write("Survolez et zoomez sur la carte pour apprendre les noms.")
    fig_rev = px.choropleth_mapbox(
        df, geojson=df.geometry, locations=df.index,
        color=col_nom, mapbox_style="carto-positron",
        zoom=6, center={"lat": 8.6, "lon": 1.2},
        opacity=0.6, hover_name=col_nom
    )
    fig_rev.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    st.plotly_chart(fig_rev, use_container_width=True)

with tab2:
    if not st.session_state.termine:
        if st.session_state.nb_questions < 5:
            if st.button("🎯 Nouvelle Question"):
                st.session_state.cible = random.choice(df[col_nom].unique().tolist())
                st.session_state.debut_temps = time.time()
            
            if st.session_state.cible:
                # Chronomètre
                t_restant = max(0, 15 - int(time.time() - st.session_state.get('debut_temps', time.time())))
                st.progress(t_restant / 15)
                st.write(f"⏳ Temps restant : **{t_restant}s**")

                # Carte de Question Interactive (Zoomable)
                df['color_quiz'] = df[col_nom].apply(lambda x: 'Cible' if x == st.session_state.cible else 'Autre')
                fig_q = px.choropleth_mapbox(
                    df, geojson=df.geometry, locations=df.index,
                    color='color_quiz', mapbox_style="carto-positron",
                    color_discrete_map={'Cible': 'red', 'Autre': 'whitesmoke'},
                    zoom=6.5, center={"lat": 8.6, "lon": 1.2}, opacity=0.8
                )
                fig_q.update_layout(margin={"r":0,"t":0,"l":0,"b":0}, showlegend=False)
                st.plotly_chart(fig_q, use_container_width=True)

                reponse = st.text_input("Votre réponse :", key=f"ans_{st.session_state.nb_questions}")
                if st.button("Valider ✅"):
                    if t_restant > 0 and normaliser(reponse) == normaliser(st.session_state.cible):
                        st.success("Bravo !")
                        st.session_state.score += 1
                    else:
                        st.error(f"Raté ! C'était {st.session_state.cible}")
                    st.session_state.nb_questions += 1
                    st.rerun()
        else:
            st.session_state.termine = True

    if st.session_state.termine:
        st.balloons()
        st.header(f"🏆 Score Final : {st.session_state.score}/5")
        nom = st.text_input("Nom pour le certificat :")
        if nom and st.button("🎓 Générer mon Certificat PDF"):
            pdf = FPDF()
            pdf.add_page()
            pdf.set_draw_color(0, 102, 51)
            pdf.rect(10, 10, 190, 277)
            pdf.ln(40)
            pdf.set_font("Arial", 'B', 30)
            pdf.cell(190, 20, "CERTIFICAT DE RÉUSSITE", ln=True, align='C')
            pdf.ln(20)
            pdf.set_font("Arial", '', 18)
            pdf.cell(190, 10, f"Décerné à {nom.upper()}", ln=True, align='C')
            pdf.cell(190, 10, f"Score : {st.session_state.score}/5", ln=True, align='C')
            pdf.ln(50)
            pdf.set_font("Arial", 'I', 12)
            pdf.cell(190, 10, f"JCDC TOGO - Direction Sylvestre BOCCO - {time.strftime('%d/%m/%Y')}", align='C')
            pdf.output("certif.pdf")
            with open("certif.pdf", "rb") as f:
                st.download_button("⬇️ Télécharger le PDF", f, "Certificat_Togo.pdf")