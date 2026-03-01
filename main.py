import geopandas as gpd
import matplotlib.pyplot as plt
import os
import random
import time
from fpdf import FPDF

# --- CONFIGURATION ---
PATH_COMMUNES = os.path.join("data", "Communes_Togo.shp")
PATH_PREFECTURES = os.path.join("data", "Prefectures_Togo.shp")
SCORE_FILE = "meilleur_score.txt"

def charger_donnees(chemin, type_jeu):
    try:
        data = gpd.read_file(chemin)
        col_nom = 'ADM2_FR' if type_jeu == "1" else 'Communes'
        
        if col_nom not in data.columns:
            for c in data.columns:
                if data[c].dtype == 'object' and c.lower() not in ['geometry', 'type']:
                    col_nom = c
                    break
        
        # Nettoyage des données pour éviter les "nan"
        data = data.dropna(subset=[col_nom])
        data[col_nom] = data[col_nom].astype(str).str.strip()
        return data, col_nom
    except Exception as e:
        print(f"Erreur de lecture : {e}")
        return None, None

def generer_certificat(nom_joueur, score, total):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 24)
    pdf.cell(200, 20, "CERTIFICAT DE REUSSITE", ln=True, align='C')
    pdf.ln(10)
    pdf.set_font("Arial", '', 16)
    pdf.multi_cell(0, 10, f"Felicitations a {nom_joueur} pour sa maitrise de la cartographie du Togo.")
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 20)
    pdf.cell(0, 10, f"SCORE : {score} / {total}", ln=True, align='C')
    pdf.ln(20)
    pdf.set_font("Arial", 'I', 12)
    pdf.cell(0, 10, "Logiciel cree par Sylvestre BOCCO", ln=True, align='R')
    nom_pdf = f"Certificat_Sylvestre_{int(time.time())}.pdf"
    pdf.output(nom_pdf)
    print(f"\n✅ Certificat cree : {nom_pdf}")

def phase_revision_clic(df, col_nom):
    print(f"\n--- 📖 REVISION INTERACTIVE (SYLVESTRE BOCCO) ---")
    fig, ax = plt.subplots(figsize=(10, 12))
    df.plot(ax=ax, cmap='Pastel1', edgecolor='black', linewidth=0.4)
    plt.title("Cliquez pour apprendre ! (Fermez pour jouer)", fontsize=14)
    plt.axis('off')

    def on_click(event):
        if event.inaxes == ax:
            for _, row in df.iterrows():
                if row.geometry.contains(gpd.points_from_xy([event.xdata], [event.ydata])[0]):
                    ax.text(event.xdata, event.ydata, row[col_nom], fontsize=9, 
                            fontweight='bold', color='darkred', bbox=dict(facecolor='white', alpha=0.7))
                    fig.canvas.draw()
                    break
    fig.canvas.mpl_connect('button_press_event', on_click)
    plt.show()

def jouer():
    print("\n" + "="*50)
    print("   🌍 TOGO MAP QUIZ CHRONO - SYLVESTRE BOCCO 🌍   ")
    print("="*50)
    
    choix = input("1. Préfectures\n2. Communes\nVotre choix : ")
    path = PATH_PREFECTURES if choix == "1" else PATH_COMMUNES
    df, col_nom = charger_donnees(path, choix)

    if df is not None:
        phase_revision_clic(df, col_nom)
        
        score = 0
        total = 5
        temps_max = 15

        for i in range(total):
            cible = random.choice(df[col_nom].unique().tolist())
            fig, ax = plt.subplots(figsize=(8, 10))
            df.plot(ax=ax, color='white', edgecolor='black', linewidth=0.5)
            df[df[col_nom] == cible].plot(ax=ax, color='red')
            
            # Affichage du chronomètre dans le titre
            plt.title(f"Question {i+1}/{total} - CHRONO: {temps_max}s\nTrouvez la zone rouge !", fontsize=14)
            plt.axis('off')
            ax.set_aspect('equal')
            plt.show(block=False)
            
            print(f"\n⏱️ Question {i+1} : Vous avez {temps_max}s !")
            debut = time.time()
            rep = input("Réponse : ")
            temps_pris = time.time() - debut

            # --- VALIDATION INTELLIGENTE ---
            reponse_user = rep.strip().lower()
            reponse_vrai = cible.strip().lower()

            if temps_pris > temps_max:
                print(f"⏰ TROP TARD ! ({int(temps_pris)}s). La réponse était : {cible}")
            elif reponse_user == reponse_vrai:
                print(f"✨ BRAVO ! Validé en {int(temps_pris)}s.")
                score += 1
            else:
                print(f"❌ FAUX ! Vous avez mis '{rep}', mais c'était : {cible}")
            
            plt.close(fig)

        print(f"\n🏆 SCORE FINAL : {score} / {total}")
        
        if input("\nVoulez-vous votre certificat PDF ? (o/n) : ").lower() == 'o':
            nom = input("Nom complet pour le certificat : ")
            generer_certificat(nom, score, total)

def main():
    while True:
        jouer()
        if input("\nVoulez-vous rejouer ? (o/n) : ").lower() != 'o':
            print("\nMerci d'avoir utilisé l'outil de Sylvestre BOCCO ! A bientôt.")
            break

if __name__ == "__main__":
    main()