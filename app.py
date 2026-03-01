import streamlit as st
import geopandas as gpd
import matplotlib.pyplot as plt
import random
import time
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
    return data, col

# --- INITIALISATION DU SCORE ET DES QUESTIONS ---
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'nb_q' not in st.session_state:
    st.session_state.nb_q = 0
if 'cible' not in st.session_state:
    st.session_state.cible = None
if 'termine' not in st.session_state:
    st.session_state.termine = False

# --- BARRE LATÉRALE PROFESSIONNELLE ---
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
    # Ajustement automatique des noms de fichiers
    path = f"data/{niveau}_Togo.shp"
    
    if st.button("🔄 Recommencer"):
        for key in st.session_state.keys():
            del st.session_state[key]
        st.rerun()

df, col_nom = charger_donnees(path, niveau)

# --- ZONE DE JEU ---
st.title("🌍 Quiz Cartographique du Togo")

if not st.session_state.termine:
    if st.session_state.nb_q < 5:
        # Affichage clair de la progression
        st.info(f"Question **{st.session_state.nb_q + 1}** sur 5  |  Votre Score actuel : **{st.session_state.score}**")
        
        if st.session_state.cible is None:
            st.session_state.cible = random.choice(df[col_nom].unique().tolist())
        
        # Carte Matplotlib : Rapide et stable
        fig, ax = plt.subplots(figsize=(7, 9))
        df.plot(ax=ax, color='whitesmoke', edgecolor='black', linewidth=0.6)
        df[df[col_nom] == st.session_state.cible].plot(ax=ax, color='red')
        plt.axis('off')
        st.pyplot(fig)

        # Formulaire de réponse
        with st.form(key=f"form_{st.session_state.nb_q}"):
            reponse = st.text_input("Quelle est la zone en rouge ?")
            valider = st.form_submit_button("Valider ✅")
            
            if valider:
                if normaliser(reponse) == normaliser(st.session_state.cible):
                    st.success(f"Excellent ! C'est bien : {st.session_state.cible}")
                    st.session_state.score += 1
                else:
                    st.error(f"Dommage... La réponse était : {st.session_state.cible}")
                
                st.session_state.nb_q += 1
                st.session_state.cible = None # Pour changer de zone à la prochaine étape
                time.sleep(1.5)
                st.rerun()
    else:
        st.session_state.termine = True
        st.rerun()

# --- ÉCRAN FINAL ---
else:
    st.balloons()
    st.header(f"🏁 Quiz Terminé !")
    st.subheader(f"Votre score final : {st.session_state.score} / 5")
    
    nom_certif = st.text_input("Entrez votre nom pour le certificat :")
    if nom_certif and st.button("🎓 Générer mon Certificat"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_draw_color(0, 102, 51)
        pdf.rect(10, 10, 190, 277)
        pdf.ln(50)
        pdf.set_font("Arial", 'B', 25)
        pdf.cell(190, 10, "CERTIFICAT DE RÉUSSITE", ln=True, align='C')
        pdf.ln(20)
        pdf.set_font("Arial", '', 15)
        pdf.cell(190, 10, f"Décerné à : {nom_certif.upper()}", ln=True, align='C')
        pdf.ln(40)
        pdf.cell(190, 10, f"Pour sa maîtrise de la carte des {niveau} du Togo.", ln=True, align='C')
        pdf.ln(60)
        pdf.set_font("Arial", 'I', 10)
        pdf.cell(190, 10, f"JCDC TOGO - Direction Sylvestre BOCCO - {time.strftime('%d/%m/%Y')}", align='C')
        pdf.output("certif.pdf")
        
        with open("certif.pdf", "rb") as f:
            st.download_button("⬇️ Télécharger le Certificat (PDF)", f, "Certificat_Togo_JCDC.pdf")