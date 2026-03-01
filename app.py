import streamlit as st
import geopandas as gpd
import matplotlib.pyplot as plt
import plotly.express as px
import random
import time
from fpdf import FPDF
from unidecode import unidecode
from PIL import Image

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Togo Map Quiz - JCDC TOGO", layout="wide")

def normaliser(texte):
    return unidecode(str(texte)).strip().lower()

@st.cache_data
def charger_donnees(path, niveau):
    data = gpd.read_file(path)
    col = 'ADM2_FR' if niveau == "Préfectures" else 'Communes'
    data = data.dropna(subset=[col])
    # Version WGS84 pour le zoom Plotly en révision
    data_gps = data.to_crs(epsg=4326)
    return data, data_gps, col

# --- INITIALISATION DES VARIABLES D'ÉTAT ---
if 'score' not in st.session_state: st.session_state.score = 0
if 'nb_q' not in st.session_state: st.session_state.nb_q = 0
if 'cible' not in st.session_state: st.session_state.cible = None
if 'termine' not in st.session_state: st.session_state.termine = False

# --- BARRE LATÉRALE (BRANDING JCDC) ---
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
    niveau = st.selectbox("Choisir l'échelle", ["Préfectures", "Communes"])
    path = f"data/{niveau}_Togo.shp"
    
    if st.button("🔄 Réinitialiser le Quiz"):
        for key in ["score", "nb_q", "termine"]: st.session_state[key] = 0 if key != "termine" else False
        st.session_state.cible = None
        st.rerun()

# Chargement des données
try:
    df, df_gps, col_nom = charger_donnees(path, niveau)
except Exception as e:
    st.error(f"Erreur de chargement des données SIG : {e}")
    st.stop()

# --- INTERFACE PRINCIPALE ---
st.title("🌍 Togo Map Quiz Interactif")
tab1, tab2 = st.tabs(["📖 Phase de Révision (Zoom)", "🎮 Défi Chronométré (Rapide)"])

# --- ONGLET 1 : RÉVISION (INTERACTIF) ---
with tab1:
    st.subheader("Explorez et apprenez avant de jouer")
    fig_rev = px.choropleth_mapbox(
        df_gps, geojson=df_gps.geometry, locations=df_gps.index,
        color=col_nom, mapbox_style="carto-positron",
        zoom=6, center={"lat": 8.6, "lon": 1.2},
        opacity=0.5, hover_name=col_nom
    )
    fig_rev.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
    st.plotly_chart(fig_rev, use_container_width=True)

# --- ONGLET 2 : QUIZ (FLUIDE) ---
with tab2:
    if not st.session_state.termine:
        if st.session_state.nb_q < 5:
            st.info(f"Progression : **{st.session_state.nb_q + 1} / 5** |  Score : **{st.session_state.score}**")
            
            if st.session_state.cible is None:
                st.session_state.cible = random.choice(df[col_nom].unique().tolist())
            
            # Carte Statique Matplotlib (Rapide, pas de beug)
            fig, ax = plt.subplots(figsize=(6, 8))
            df.plot(ax=ax, color='whitesmoke', edgecolor='black', linewidth=0.5)
            df[df[col_nom] == st.session_state.cible].plot(ax=ax, color='red')
            plt.axis('off')
            st.pyplot(fig)

            with st.form(key=f"form_quiz_{st.session_state.nb_q}"):
                reponse = st.text_input("Quelle est la zone affichée en rouge ?")
                if st.form_submit_button("Valider la réponse ✅"):
                    if normaliser(reponse) == normaliser(st.session_state.cible):
                        st.success(f"Bravo ! C'est bien {st.session_state.cible}")
                        st.session_state.score += 1
                    else:
                        st.error(f"Dommage... C'était {st.session_state.cible}")
                    
                    st.session_state.nb_q += 1
                    st.session_state.cible = None
                    time.sleep(1.2)
                    st.rerun()
        else:
            st.session_state.termine = True
            st.rerun()

    # --- ÉCRAN FINAL ET ATTESTATION ---
    else:
        st.balloons()
        st.header(f"🏁 Quiz Terminé ! Votre score : {st.session_state.score}/5")
        
        nom_complet = st.text_input("Saisissez votre Nom et Prénom pour l'attestation :")
        
        if nom_complet:
            if st.button("🎓 Générer mon Attestation JCDC"):
                pdf = FPDF(orientation='L', unit='mm', format='A4')
                pdf.add_page()
                
                # Design : Bordures Vert/Jaune Togo
                pdf.set_draw_color(0, 106, 77); pdf.set_line_width(2)
                pdf.rect(5, 5, 287, 200)
                pdf.set_draw_color(255, 206, 0); pdf.set_line_width(1)
                pdf.rect(10, 10, 277, 190)

                # Logos
                try:
                    pdf.image("assets/logo_jcdc.png", 20, 20, 35)
                    pdf.image("assets/drapeau_togo.png", 240, 20, 35)
                except: pass

                # Texte du certificat
                pdf.set_y(65)
                pdf.set_font("Arial", 'B', 35); pdf.set_text_color(0, 106, 77)
                pdf.cell(0, 20, "CERTIFICAT DE RÉUSSITE", ln=True, align='C')
                
                pdf.ln(10); pdf.set_font("Arial", 'I', 20); pdf.set_text_color(0, 0, 0)
                pdf.cell(0, 10, "Ce titre est fièrement décerné à :", ln=True, align='C')
                
                pdf.ln(10); pdf.set_font("Arial", 'B', 30); pdf.set_text_color(216, 12, 18)
                pdf.cell(0, 20, nom_complet.upper(), ln=True, align='C')
                
                pdf.ln(10); pdf.set_font("Arial", '', 18); pdf.set_text_color(0, 0, 0)
                pdf.multi_cell(0, 10, f"Pour sa maîtrise de la carte des {niveau} du Togo\nScore Final : {st.session_state.score} / 5", align='C')
                
                pdf.set_y(165); pdf.set_font("Arial", 'B', 14)
                pdf.cell(0, 10, f"Fait le {time.strftime('%d/%m/%Y')} | Direction JCDC TOGO", ln=True, align='C')
                pdf.cell(0, 10, "Sylvestre BOCCO", ln=True, align='C')
                
                output_path = "Attestation_Togo_JCDC.pdf"
                pdf.output(output_path)
                
                with open(output_path, "rb") as f:
                    st.download_button("⬇️ Télécharger mon Attestation (PDF)", f, file_name=f"Attestation_{nom_complet}.pdf")