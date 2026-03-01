import streamlit as st
import geopandas as gpd
import matplotlib.pyplot as plt
import random
import time
import os
from fpdf import FPDF
from unidecode import unidecode

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Togo Map Quiz - Sylvestre BOCCO", layout="wide")

# Fonction pour ignorer les accents et majuscules lors de la vérification
def normaliser(texte):
    return unidecode(str(texte)).strip().lower()

@st.cache_data
def charger_donnees(chemin, type_jeu):
    try:
        data = gpd.read_file(chemin)
        # Utilisation des colonnes identifiées dans QGIS par Sylvestre
        col_nom = 'ADM2_FR' if type_jeu == "Préfectures" else 'Communes'
        data = data.dropna(subset=[col_nom])
        data[col_nom] = data[col_nom].astype(str).str.strip()
        return data, col_nom
    except Exception as e:
        st.error(f"Erreur de chargement : {e}")
        return None, None

# --- INITIALISATION DU JEU ---
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'nb_questions' not in st.session_state:
    st.session_state.nb_questions = 0
if 'cible' not in st.session_state:
    st.session_state.cible = None
if 'termine' not in st.session_state:
    st.session_state.termine = False

# --- INTERFACE PRINCIPALE ---
st.title("🌍 Quiz Cartographique du Togo")
st.write("Application développée par **Sylvestre BOCCO** (JCDC TOGO)")

with st.sidebar:
    st.header("⚙️ Configuration")
    niveau = st.selectbox("Choisir le niveau", ["Préfectures", "Communes"])
    path = "data/Prefectures_Togo.shp" if niveau == "Préfectures" else "data/Communes_Togo.shp"
    
    if st.button("🔄 Recommencer le Jeu"):
        st.session_state.score = 0
        st.session_state.nb_questions = 0
        st.session_state.termine = False
        st.session_state.cible = None
        st.rerun()

df, col_nom = charger_donnees(path, niveau)

# --- NAVIGATION ---
tab1, tab2 = st.tabs(["📖 Phase de Révision", "🎮 Défi Chronométré"])

with tab1:
    st.subheader("Étudiez la carte du Togo")
    fig_rev, ax_rev = plt.subplots(figsize=(10, 12))
    df.plot(ax=ax_rev, cmap='Set3', edgecolor='black', linewidth=0.5)
    # Affichage des étiquettes pour la révision
    for x, y, label in zip(df.geometry.centroid.x, df.geometry.centroid.y, df[col_nom]):
        ax_rev.text(x, y, label, fontsize=6, ha='center', fontweight='bold', bbox=dict(facecolor='white', alpha=0.5, edgecolor='none'))
    plt.axis('off')
    st.pyplot(fig_rev)

with tab2:
    if not st.session_state.termine:
        if st.session_state.nb_questions < 5:
            if st.button("🎯 Question Suivante"):
                st.session_state.cible = random.choice(df[col_nom].unique().tolist())
                st.session_state.debut_temps = time.time()
            
            if st.session_state.cible:
                # Gestion du Chronomètre
                temps_restant = max(0, 30 - int(time.time() - st.session_state.get('debut_temps', time.time())))
                
                if temps_restant > 0:
                    st.warning(f"⏳ Temps restant : {temps_restant} secondes")
                else:
                    st.error("⏰ Temps écoulé !")

                # Affichage de la carte de question
                fig, ax = plt.subplots(figsize=(8, 10))
                df.plot(ax=ax, color='whitesmoke', edgecolor='black')
                df[df[col_nom] == st.session_state.cible].plot(ax=ax, color='red')
                plt.axis('off')
                st.pyplot(fig)

                # Saisie de la réponse
                reponse = st.text_input(f"Question {st.session_state.nb_questions + 1}/5 : Quelle zone est en rouge ?", key=f"input_{st.session_state.nb_questions}")
                
                if st.button("Vérifier ✅"):
                    if temps_restant <= 0:
                        st.error(f"Trop lent ! La réponse était : {st.session_state.cible}")
                    elif normaliser(reponse) == normaliser(st.session_state.cible):
                        st.success("✨ Excellent ! Bonne réponse.")
                        st.session_state.score += 1
                    else:
                        st.error(f"❌ Dommage... C'était : {st.session_state.cible}")
                    
                    st.session_state.nb_questions += 1
                    time.sleep(1) # Petit délai pour lire le résultat
                    st.rerun()
        else:
            st.session_state.termine = True

    # --- ÉCRAN FINAL ET CERTIFICAT ---
    if st.session_state.termine:
        st.balloons()
        st.header(f"🏁 Fin du Quiz ! Score : {st.session_state.score} / 5")
        
        if st.session_state.score >= 3:
            st.write("---")
            st.subheader("🎓 Obtenez votre Certificat")
            nom_utilisateur = st.text_input("Entrez votre NOM et PRÉNOM complet :")
            
            if nom_utilisateur:
                if st.button("📄 Créer mon Certificat"):
                    pdf = FPDF()
                    pdf.add_page()
                    # Bordure décorative
                    pdf.set_draw_color(0, 100, 0)
                    pdf.rect(10, 10, 190, 277, 'D')
                    
                    pdf.ln(30)
                    pdf.set_font("Arial", 'B', 30)
                    pdf.cell(200, 20, "CERTIFICAT DE RÉUSSITE", ln=True, align='C')
                    
                    pdf.ln(20)
                    pdf.set_font("Arial", '', 18)
                    pdf.cell(200, 10, "Décerné avec fierté à :", ln=True, align='C')
                    
                    pdf.ln(10)
                    pdf.set_font("Arial", 'B', 25)
                    pdf.set_text_color(200, 0, 0) # Nom en rouge
                    pdf.cell(200, 20, nom_utilisateur.upper(), ln=True, align='C')
                    
                    pdf.set_text_color(0, 0, 0)
                    pdf.ln(15)
                    pdf.set_font("Arial", '', 16)
                    pdf.multi_cell(0, 10, f"Pour avoir démontré une excellente connaissance de la géographie du Togo lors du Quiz Cartographique.\nScore final : {st.session_state.score}/5", align='C')
                    
                    pdf.ln(40)
                    pdf.set_font("Arial", 'I', 12)
                    pdf.cell(0, 10, f"Système conçu par Sylvestre BOCCO | Date : {time.strftime('%d/%m/%Y')}", ln=True, align='C')
                    
                    temp_file = "certif_final.pdf"
                    pdf.output(temp_file)
                    
                    with open(temp_file, "rb") as f:
                        st.download_button(
                            label="⬇️ Télécharger mon Certificat (PDF)",
                            data=f,
                            file_name=f"Certificat_{nom_utilisateur.replace(' ', '_')}.pdf",
                            mime="application/pdf"
                        )
            else:
                st.info("Veuillez saisir votre nom pour débloquer le certificat.")
        else:
            st.warning("Score insuffisant pour le certificat. Retentez votre chance !")

st.sidebar.markdown("---")
st.sidebar.write(f"📈 Score : {st.session_state.score}/5")