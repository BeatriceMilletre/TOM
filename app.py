import streamlit as st
import json
import os
import secrets
import smtplib
from email.message import EmailMessage
from datetime import datetime
from typing import Tuple

# ==============================
# CONFIGURATION EMAIL
# ==============================

email_conf = st.secrets["email"]

EMAIL_HOST = email_conf.get("host", "smtp.gmail.com")
EMAIL_PORT = email_conf.get("port", 587)
EMAIL_USERNAME = email_conf.get("username")
EMAIL_PASSWORD = email_conf.get("password")
EMAIL_USE_TLS = email_conf.get("use_tls", True)

PRACTITIONER_EMAIL = EMAIL_USERNAME

# ==============================
# STOCKAGE LOCAL (SECONDAIRE)
# ==============================

DATA_DIR = "data"
DATA_FILE = os.path.join(DATA_DIR, "competences_sociales.json")
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
# ENVOI EMAIL AVEC PJ JSON
# ==============================

def send_results_by_email(code: str, payload: dict) -> Tuple[bool, str]:

    if not all([EMAIL_HOST, EMAIL_PORT, EMAIL_USERNAME, EMAIL_PASSWORD]):
        return False, "Configuration email incomplète."

    try:
        msg = EmailMessage()
        msg["Subject"] = f"Compétences sociales – Nouvelle passation ({code})"
        msg["From"] = EMAIL_USERNAME
        msg["To"] = PRACTITIONER_EMAIL

        msg.set_content(
            "Une nouvelle passation du questionnaire « Compétences sociales – Adolescents / Adultes » a été complétée.\n\n"
            f"Code : {code}\n"
            f"Date : {datetime.now().strftime('%d/%m/%Y %H:%M')}\n\n"
            "Les données complètes (questions, réponses, scores) sont jointes en pièce jointe (JSON).\n"
        )

        json_bytes = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")

        msg.add_attachment(
            json_bytes,
            maintype="application",
            subtype="json",
            filename=f"competences_sociales_{code}.json",
        )

        smtp = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT, timeout=20)
        smtp.ehlo()
        if EMAIL_USE_TLS:
            smtp.starttls()
            smtp.ehlo()

        smtp.login(EMAIL_USERNAME, EMAIL_PASSWORD)
        smtp.send_message(msg)
        smtp.quit()

        return True, "Résultats envoyés automatiquement au praticien."

    except Exception as e:
        return False, f"Erreur email : {e}"


# ==============================
# QUESTIONNAIRE
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
    {"id": 1, "domain": "Compréhension sociale",
     "label": "Je comprends facilement l’émotion de quelqu’un (colère, tristesse, gêne…).",
     "help": "Exemple : ton interlocuteur répond sèchement → il est contrarié."},
    {"id": 2, "domain": "Compréhension sociale",
     "label": "Je repère quand quelqu’un ne veut plus parler ou veut changer de sujet.",
     "help": "Exemple : soupirs, regard ailleurs."},
    {"id": 3, "domain": "Compréhension sociale",
     "label": "Je comprends si quelqu’un plaisante ou parle sérieusement.",
     "help": "Exemple : sarcasme, ironie."},
    {"id": 4, "domain": "Compréhension sociale",
     "label": "Je remarque quand quelqu’un n’est pas honnête ou exagère.",
     "help": "Exemple : incohérences."},
    {"id": 5, "domain": "Compréhension sociale",
     "label": "Je comprends l’intention derrière ce que l’on me dit.",
     "help": "Exemple : sous-entendu."},
    {"id": 6, "domain": "Compréhension sociale",
     "label": "Je peux deviner ce qu’une personne pense dans une situation donnée.",
     "help": "Exemple : évitement du regard."},
    {"id": 7, "domain": "Compréhension sociale",
     "label": "Je comprends ce que l’on attend de moi dans un groupe.",
     "help": "Exemple : rôle implicite."},

    {"id": 8, "domain": "Communication sociale",
     "label": "J’arrive à entrer dans une conversation sans interrompre.",
     "help": "Exemple : j’attends une pause."},
    {"id": 9, "domain": "Communication sociale",
     "label": "Je sais terminer une conversation sans être brusque.",
     "help": "Exemple : formule de sortie."},
    {"id": 10, "domain": "Communication sociale",
     "label": "Je ne parle pas trop longtemps du même sujet.",
     "help": "Exemple : je synthétise."},
    {"id": 11, "domain": "Communication sociale",
     "label": "Je m’adapte à la personne à qui je parle.",
     "help": "Exemple : registre différent."},
    {"id": 12, "domain": "Communication sociale",
     "label": "Je sais quand parler et quand écouter.",
     "help": "Exemple : je ne coupe pas."},
    {"id": 13, "domain": "Communication sociale",
     "label": "Je pose des questions pour faire avancer la conversation.",
     "help": "Exemple : relance."},
    {"id": 14, "domain": "Communication sociale",
     "label": "Je résume ce que l’autre dit pour vérifier que j’ai compris.",
     "help": "Exemple : reformulation."},
    {"id": 15, "domain": "Communication sociale",
     "label": "Je repère quand un sujet met quelqu’un mal à l’aise.",
     "help": "Exemple : évitement."},

    {"id": 16, "domain": "Régulation émotionnelle",
     "label": "Je garde mon calme dans les situations sociales compliquées.",
     "help": "Exemple : conflit."},
    {"id": 17, "domain": "Régulation émotionnelle",
     "label": "Je peux demander une pause quand je suis stressé(e).",
     "help": "Exemple : temps de récupération."},
    {"id": 18, "domain": "Régulation émotionnelle",
     "label": "Je ne m’énerve pas trop vite quand on me contredit.",
     "help": "Exemple : discussion."},
    {"id": 19, "domain": "Régulation émotionnelle",
     "label": "Je sais comment me calmer après un conflit.",
     "help": "Exemple : respiration."},
    {"id": 20, "domain": "Régulation émotionnelle",
     "label": "Je gère bien les critiques, même injustes.",
     "help": "Exemple : prise de recul."},
    {"id": 21, "domain": "Régulation émotionnelle",
     "label": "Je peux dire non sans agressivité ni soumission.",
     "help": "Exemple : affirmation de soi."},

    {"id": 22, "domain": "Flexibilité sociale",
     "label": "Je peux changer de plan si nécessaire.",
     "help": "Exemple : adaptation."},
    {"id": 23, "domain": "Flexibilité sociale",
     "label": "J’accepte qu’on ne fasse pas comme je pensais.",
     "help": "Exemple : compromis."},
    {"id": 24, "domain": "Flexibilité sociale",
     "label": "Je comprends le point de vue des autres même s’il est différent du mien.",
     "help": "Exemple : empathie cognitive."},
    {"id": 25, "domain": "Flexibilité sociale",
     "label": "Je m’adapte à un nouveau groupe.",
     "help": "Exemple : observation préalable."},
    {"id": 26, "domain": "Flexibilité sociale",
     "label": "J’accepte qu’on change de sujet.",
     "help": "Exemple : lâcher-prise."},

    {"id": 27, "domain": "Compétences spécifiques",
     "label": "Je comprends la dynamique des groupes.",
     "help": "Exemple : leader, influence."},
    {"id": 28, "domain": "Compétences spécifiques",
     "label": "Je repère la différence entre moquerie gentille et méchante.",
     "help": "Exemple : sous-entendu."},
    {"id": 29, "domain": "Compétences spécifiques",
     "label": "Je reconnais une relation saine d’une relation toxique.",
     "help": "Exemple : manipulation."},
    {"id": 30, "domain": "Compétences spécifiques",
     "label": "Je sais me défendre sans agresser.",
     "help": "Exemple : assertivité."},
    {"id": 31, "domain": "Compétences spécifiques",
     "label": "Je sais proposer une activité ou un projet.",
     "help": "Exemple : initiative."},
    {"id": 32, "domain": "Compétences spécifiques",
     "label": "Je sais réparer un malentendu.",
     "help": "Exemple : clarification."},
    {"id": 33, "domain": "Compétences spécifiques",
     "label": "Je m’intègre sans être intrusif(ve).",
     "help": "Exemple : respect des codes."},

    {"id": 34, "domain": "Autonomie sociale",
     "label": "Je demande de l’aide quand j’en ai besoin.",
     "help": "Exemple : soutien."},
    {"id": 35, "domain": "Autonomie sociale",
     "label": "J’exprime ce que je ressens sans envahir.",
     "help": "Exemple : communication émotionnelle."},
    {"id": 36, "domain": "Autonomie sociale",
     "label": "Je gère une situation sociale imprévue.",
     "help": "Exemple : imprévus."},
    {"id": 37, "domain": "Autonomie sociale",
     "label": "Je parle avec des adultes ou professionnels sans stress excessif.",
     "help": "Exemple : rendez-vous."},
    {"id": 38, "domain": "Autonomie sociale",
     "label": "J’envoie des messages appropriés selon le contexte.",
     "help": "Exemple : registre écrit."},
    {"id": 39, "domain": "Autonomie sociale",
     "label": "Je sais refuser sans culpabiliser.",
     "help": "Exemple : limite personnelle."},
]

ITEM_TOM_LEVEL = {
    1: 0, 2: 1, 3: 4, 4: 3, 5: 1, 6: 2, 7: 3,
    8: 1, 9: 1, 10: 1, 11: 2, 12: 2, 13: 2, 14: 3, 15: 4,
    16: 0, 17: 0, 18: 2, 19: 2, 20: 3, 21: 3,
    22: 1, 23: 1, 24: 2, 25: 3, 26: 3,
    27: 3, 28: 4, 29: 4, 30: 2, 31: 1, 32: 4, 33: 3,
    34: 1, 35: 2, 36: 2, 37: 3, 38: 3, 39: 4,
}


def compute_scores(responses):
    domain_scores = {d: 0 for d in DOMAINS}
    domain_max = {
        "Compréhension sociale": 21,
        "Communication sociale": 24,
        "Régulation émotionnelle": 18,
        "Flexibilité sociale": 15,
        "Compétences spécifiques": 21,
        "Autonomie sociale": 18,
    }

    total_score = 0
    for item in ITEMS:
        val = responses.get(item["id"], 0)
        domain_scores[item["domain"]] += val
        total_score += val

    total_max = len(ITEMS) * 3

    tom_scores = {l: 0 for l in range(6)}
    tom_max = {l: 0 for l in range(6)}

    for qid, val in responses.items():
        level = ITEM_TOM_LEVEL.get(qid)
        if level is not None:
            tom_scores[level] += val
            tom_max[level] += 3

    tom_level = max(range(6), key=lambda l: tom_scores[l] / tom_max[l] if tom_max[l] else 0)

    return domain_scores, domain_max, total_score, total_max, tom_level


# ==============================
# INTERFACE
# ==============================

st.set_page_config(page_title="Compétences sociales", page_icon="🧠")
st.title("🧠 Questionnaire de compétences sociales")
st.caption("Adolescents / Adultes – Passation anonyme")

responses = {}

st.write("0 = jamais · 1 = parfois · 2 = souvent · 3 = toujours")

for item in ITEMS:
    responses[item["id"]] = st.radio(
        f"{item['id']}. {item['label']}",
        [0, 1, 2, 3],
        index=1,
        horizontal=True,
        help=item["help"],
        key=f"q{item['id']}",
    )

if st.button("Envoyer le questionnaire", type="primary"):

    domain_scores, domain_max, total_score, total_max, tom_level = compute_scores(responses)
    code = "CS-" + secrets.token_hex(3).upper()

    # ➜ JSON COMPLET AVEC ÉNONCÉS
    detailed_responses = []
    for item in ITEMS:
        detailed_responses.append({
            "id": item["id"],
            "domain": item["domain"],
            "question": item["label"],
            "help": item["help"],
            "response": responses.get(item["id"], 0),
            "scale": "0=jamais, 1=parfois, 2=souvent, 3=toujours",
        })

    payload = {
        "questionnaire": "Compétences sociales – Adolescents / Adultes",
        "code": code,
        "date": datetime.now().isoformat(),
        "items": detailed_responses,
        "scores": {
            "domain_scores": domain_scores,
            "domain_max": domain_max,
            "total_score": total_score,
            "total_max": total_max,
            "tom_level": tom_level,
        },
    }

    data = load_data()
    data[code] = payload
    save_data(data)

    ok, msg = send_results_by_email(code, payload)

    if ok:
        st.success("Questionnaire envoyé. Merci.")
    else:
        st.error(msg)
