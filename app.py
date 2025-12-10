import streamlit as st
import json
import os
import secrets
import smtplib
import ssl
from datetime import datetime

# ==============================
# CONFIGURATION EMAIL
# ==============================

EMAIL_SENDER = "beatricemilletre@gmail.com"          # expéditeur (Gmail)
EMAIL_APP_PASSWORD = "TON_MOT_DE_PASSE_APP_ICI"      # mot de passe d’application
PRACTITIONER_EMAIL = "beatricemilletre@gmail.com"    # destinataire (praticien)

# ==============================
# CHEMIN DE STOCKAGE DES DONNÉES
# ==============================

DATA_DIR = "data"
DATA_FILE = os.path.join(DATA_DIR, "social_comp_ado_adulte.json")

os.makedirs(DATA_DIR, exist_ok=True)


def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {}
    return {}


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


# ==============================
# DÉFINITION DU QUESTIONNAIRE
# ==============================

DOMAINS = [
    "Compréhension sociale",
    "Communication sociale",
    "Régulation émotionnelle",
    "Flexibilité sociale",
    "Compétences spécifiques",
    "Autonomie sociale",
]

ITEMS = [
    # 1. Compréhension sociale (1–7)
    {"id": 1, "domain": "Compréhension sociale",
     "label": "Je comprends facilement l’émotion de quelqu’un (colère, tristesse, gêne…).",
     "help": "Exemple : ton interlocuteur répond sèchement → « Il est contrarié. »"},
    {"id": 2, "domain": "Compréhension sociale",
     "label": "Je repère quand quelqu’un ne veut plus parler ou veut changer de sujet.",
     "help": "Exemple : soupirs, regarde ailleurs, consulte sa montre."},
    {"id": 3, "domain": "Compréhension sociale",
     "label": "Je comprends si quelqu’un plaisante ou parle sérieusement.",
     "help": "Exemple : sarcasme, ironie, ton exagéré."},
    {"id": 4, "domain": "Compréhension sociale",
     "label": "Je remarque quand quelqu’un n’est pas honnête ou exagère.",
     "help": "Exemple : histoire incohérente, détails qui changent."},
    {"id": 5, "domain": "Compréhension sociale",
     "label": "Je comprends l’intention derrière ce que l’on me dit.",
     "help": "Exemple : « Ton rapport est… original » = insatisfaction."},
    {"id": 6, "domain": "Compréhension sociale",
     "label": "Je peux deviner ce qu’une personne pense dans une situation donnée.",
     "help": "Exemple : évite ton regard → probable désaccord."},
    {"id": 7, "domain": "Compréhension sociale",
     "label": "Je comprends ce que l’on attend de moi dans un groupe.",
     "help": "Exemple : tout le monde attend qu’un membre lance le projet."},

    # 2. Communication sociale (8–15)
    {"id": 8, "domain": "Communication sociale",
     "label": "J’arrive à entrer dans une conversation sans interrompre.",
     "help": "Exemple : j’attends une pause naturelle pour parler."},
    {"id": 9, "domain": "Communication sociale",
     "label": "Je sais terminer une conversation sans être brusque.",
     "help": "Exemple : « Merci, je dois y aller. »"},
    {"id": 10, "domain": "Communication sociale",
     "label": "Je ne parle pas trop longtemps du même sujet.",
     "help": "Exemple : je synthétise et laisse place à l’autre."},
    {"id": 11, "domain": "Communication sociale",
     "label": "Je m’adapte à la personne à qui je parle.",
     "help": "Exemple : langage différent avec ami / professeur / supérieur."},
    {"id": 12, "domain": "Communication sociale",
     "label": "Je sais quand parler et quand écouter.",
     "help": "Exemple : je ne coupe pas quelqu’un qui explique son idée."},
    {"id": 13, "domain": "Communication sociale",
     "label": "Je pose des questions pour faire avancer la conversation.",
     "help": "Exemple : « Qu’en penses-tu ? »"},
    {"id": 14, "domain": "Communication sociale",
     "label": "Je résume ce que l’autre dit pour vérifier que j’ai compris.",
     "help": "Exemple : « Si je comprends bien, tu proposes… »"},
    {"id": 15, "domain": "Communication sociale",
     "label": "Je repère quand un sujet met quelqu’un mal à l’aise.",
     "help": "Exemple : l’autre évite le regard, change de sujet."},

    # 3. Régulation émotionnelle (16–21)
    {"id": 16, "domain": "Régulation émotionnelle",
     "label": "Je garde mon calme dans les situations sociales compliquées.",
     "help": "Exemple : je reste calme même si on me coupe la parole."},
    {"id": 17, "domain": "Régulation émotionnelle",
     "label":
