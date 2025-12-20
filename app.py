# Nécessite Flask: pip install flask
from flask import Flask, request, jsonify
from datetime import datetime
import os

app = Flask(__name__)

# Fichier pour stocker les IP (dans un vrai projet, utiliseriez une base de données)
LOG_FILE = "ips_collectees.log"

@app.route('/enregistrer-ip', methods=['POST'])
def enregistrer_ip():
    """
    Recoit les données JSON envoyées par le frontend.
    Enregistre toutes les informations dans un fichier log.
    """
    # --- Récupération des données du corps de la requête ---
    data = request.get_json()
    ip_locale_envoyee = data.get('ip_locale', 'Non fournie')
    ip_publique_envoyee = data.get('ip_publique', 'Non fournie')
    date_heure_envoyee = data.get('date_heure', 'Non fournie')
    user_agent_envoye = data.get('user_agent', 'Non fourni')

    # --- Récupération de l'IP publique réelle du visiteur (côté serveur) ---
    # Celle-ci est différente de ip_publique_envoyee si le visiteur est derrière un proxy/CDN
    if request.environ.get('HTTP_X_FORWARDED_FOR') is None:
        ip_publique_visiteur = request.environ.get('REMOTE_ADDR', 'Inconnue')
    else:
        # X-Forwarded-For peut contenir une liste d'IPs, la première est celle du client
        ip_publique_visiteur = request.environ['HTTP_X_FORWARDED_FOR'].split(',')[0].strip()

    # User-Agent vu par le serveur
    user_agent_serveur = request.headers.get('User-Agent', 'Inconnu')

    # Horodatage serveur
    horodatage_serveur = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # --- Création de l'entrée de log ---
    log_entry = (
        f"--- Nouvelle Visite (Serveur: {horodatage_serveur}) ---\n"
        f"  IP Locale (Client):     {ip_locale_envoyee}\n"
        f"  IP Publique (Client):   {ip_publique_envoyee}\n" # IP publique déduite par le client
        f"  IP Publique (Serveur):  {ip_publique_visiteur}\n" # IP réelle du client qui se connecte à ce serveur
        f"  Date/Heure (Client):    {date_heure_envoyee}\n"
        f"  User-Agent (Client):    {user_agent_envoyee}\n"
        f"  User-Agent (Serveur):   {user_agent_serveur}\n" # Normalement identique
        f"------------------------------------------\n\n"
    )

    # --- Ecriture dans le fichier log ---
    try:
        with open(LOG_FILE, "a", encoding='utf-8') as f:
            f.write(log_entry)
        print(log_entry.strip()) # Affiche aussi dans la console du serveur
        return jsonify({"status": "success", "message": "Données enregistrées"}), 200
    except Exception as e:
        print(f"Erreur lors de l'écriture dans le log: {e}")
        return jsonify({"status": "error", "message": "Erreur lors de l'enregistrement"}), 500


@app.route('/voir-ips')
def voir_ips():
    """Affiche le contenu du fichier de log dans le navigateur."""
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r", encoding='utf-8') as f:
            contenu = f.read()
        # Pour un affichage plus joli dans le navigateur
        return f"<html><head><title>IPs Collectées</title></head><body><pre>{contenu}</pre></body></html>", 200
    else:
        return "<html><body>Aucune IP enregistrée pour le moment.</body></html>", 200


# --- Point d'entrée pour vérifier que le serveur est en ligne ---
@app.route('/')
def index():
    return jsonify({
        "message": "Backend de collecte d'IPs opérationnel",
        "endpoint_enregistrement": "/enregistrer-ip",
        "endpoint_visualisation": "/voir-ips"
    })


if __name__ == '__main__':
    # Pour les déploiements en production, il vaut mieux utiliser un serveur WSGI dédié
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
