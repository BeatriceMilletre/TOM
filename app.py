import streamlit as st
import json
import os
import secrets
import smtplib
import ssl
from datetime import datetime

# ==============================
# CONFIGURATION EMAIL via st.secrets["email"]
# ==============================

email_conf = st.secrets["email"]

EMAIL_HOST = email_conf.get("host", "smtp.gmail.com")
EMAIL_PORT = email_conf.get("port", 587)
EMAIL_SENDER = email_conf.get("username")
EMAIL_APP_PASSWORD = email_conf.get("password")
USE_TLS = email_conf.get("use_tls", True)

# destinataire = toi, ou change ici si besoin
PRACTITIONER_EMAIL = EMAIL_SENDER

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
     "label": "Je peux demander une pause quand je suis stressé(e).",
     "help": "Exemple : « Je reviens dans 5 minutes. »"},
    {"id": 18, "domain": "Régulation émotionnelle",
     "label": "Je ne m’énerve pas trop vite quand on me contredit.",
     "help": "Exemple : « Explique-moi ton point de vue. »"},
    {"id": 19, "domain": "Régulation émotionnelle",
     "label": "Je sais comment me calmer après un conflit.",
     "help": "Exemple : marcher, écrire, respirer."},
    {"id": 20, "domain": "Régulation émotionnelle",
     "label": "Je gère bien les critiques, même injustes.",
     "help": "Exemple : j’écoute sans exploser."},
    {"id": 21, "domain": "Régulation émotionnelle",
     "label": "Je peux dire « non » sans être agressif(ve) ni trop gentil(le).",
     "help": "Exemple : « Non, je ne suis pas disponible. »"},

    # 4. Flexibilité sociale (22–26)
    {"id": 22, "domain": "Flexibilité sociale",
     "label": "Je peux changer de plan si nécessaire.",
     "help": "Exemple : projet annulé → je propose une alternative."},
    {"id": 23, "domain": "Flexibilité sociale",
     "label": "J’accepte qu’on ne fasse pas comme je pensais.",
     "help": "Exemple : l’équipe choisit une autre méthode."},
    {"id": 24, "domain": "Flexibilité sociale",
     "label": "Je comprends le point de vue des autres même s’il est différent du mien.",
     "help": "Exemple : préférences différentes → je m’adapte."},
    {"id": 25, "domain": "Flexibilité sociale",
     "label": "Je m’adapte à un nouveau groupe ou une nouvelle équipe.",
     "help": "Exemple : j’observe avant d’imposer mes idées."},
    {"id": 26, "domain": "Flexibilité sociale",
     "label": "J’accepte qu’on change de sujet même si je n’avais pas fini.",
     "help": "Exemple : on passe à autre chose en réunion."},

    # 5. Compétences spécifiques (27–33)
    {"id": 27, "domain": "Compétences spécifiques",
     "label": "Je comprends la dynamique des groupes (leader, suiveurs, influence).",
     "help": "Exemple : qui décide, qui influence, qui suit."},
    {"id": 28, "domain": "Compétences spécifiques",
     "label": "Je repère la différence entre une moquerie gentille et méchante.",
     "help": "Exemple : sarcasme, pique, sous-entendu."},
    {"id": 29, "domain": "Compétences spécifiques",
     "label": "Je reconnais une relation saine d’une relation toxique.",
     "help": "Exemple : soutien vs manipulation, dénigrement."},
    {"id": 30, "domain": "Compétences spécifiques",
     "label": "Je sais me défendre sans agresser quand on me cherche.",
     "help": "Exemple : « Je n’aime pas ce ton. »"},
    {"id": 31, "domain": "Compétences spécifiques",
     "label": "Je sais proposer une activité ou un projet.",
     "help": "Exemple : « Je propose qu’on fasse… »"},
    {"id": 32, "domain": "Compétences spécifiques",
     "label": "Je sais réparer un malentendu.",
     "help": "Exemple : « On s’est mal compris, clarifions. »"},
    {"id": 33, "domain": "Compétences spécifiques",
     "label": "Je m’intègre dans un groupe sans être intrusif(ve).",
     "help": "Exemple : j’observe d’abord les codes du groupe."},

    # 6. Autonomie sociale (34–39)
    {"id": 34, "domain": "Autonomie sociale",
     "label": "Je demande de l’aide quand j’en ai besoin.",
     "help": "Exemple : demander une explication, un soutien."},
    {"id": 35, "domain": "Autonomie sociale",
     "label": "J’exprime ce que je ressens sans envahir l’autre.",
     "help": "Exemple : « Je suis stressé(e), j’ai besoin d’aide. »"},
    {"id": 36, "domain": "Autonomie sociale",
     "label": "Je gère une situation sociale imprévue.",
     "help": "Exemple : retard, annulation, changement de plan."},
    {"id": 37, "domain": "Autonomie sociale",
     "label": "Je peux parler avec des adultes ou des professionnels sans stress excessif.",
     "help": "Exemple : service client, enseignant, médecin."},
    {"id": 38, "domain": "Autonomie sociale",
     "label": "J’envoie des messages appropriés selon le contexte.",
     "help": "Exemple : message amical vs professionnel."},
    {"id": 39, "domain": "Autonomie sociale",
     "label": "Je sais refuser quelque chose sans culpabiliser.",
     "help": "Exemple : « Non, je ne peux pas, mais merci. »"},
]


# ==============================
# MAPPING SIMPLE ToM
# ==============================

ITEM_TOM_LEVEL = {
    1: 0, 2: 1, 3: 4, 4: 3, 5: 1, 6: 2, 7: 3,
    8: 1, 9: 1, 10: 1, 11: 2, 12: 2, 13: 2, 14: 3, 15: 4,
    16: 0, 17: 0, 18: 2, 19: 2, 20: 3, 21: 3,
    22: 1, 23: 1, 24: 2, 25: 3, 26: 3,
    27: 3, 28: 4, 29: 4, 30: 2, 31: 1, 32: 4, 33: 3,
    34: 1, 35: 2, 36: 2, 37: 3, 38: 3, 39: 4,
}


def compute_scores(responses):
    """
    Calcule les sous-scores, le total et un niveau de ToM.
    Compatibilité clés int/str + ToM = niveau avec le meilleur ratio (0–5).
    """
    # normalisation des clés (JSON les stocke en str)
    norm_responses = {}
    for k, v in responses.items():
        try:
            qid = int(k)
        except (TypeError, ValueError):
            continue
        norm_responses[qid] = v

    # scores par domaine
    domain_scores = {d: 0 for d in DOMAINS}
    domain_max = {
        "Compréhension sociale": 7 * 3,
        "Communication sociale": 8 * 3,
        "Régulation émotionnelle": 6 * 3,
        "Flexibilité sociale": 5 * 3,
        "Compétences spécifiques": 7 * 3,
        "Autonomie sociale": 6 * 3,
    }

    total_score = 0
    for item in ITEMS:
        qid = item["id"]
        val = norm_responses.get(qid, 0)
        domain_scores[item["domain"]] += val
        total_score += val

    total_max = len(ITEMS) * 3

    # scores ToM par niveau
    tom_scores = {level: 0 for level in range(0, 6)}
    tom_max = {level: 0 for level in range(0, 6)}

    for qid, val in norm_responses.items():
        level = ITEM_TOM_LEVEL.get(qid)
        if level is not None:
            tom_scores[level] += val
            tom_max[level] += 3

    # choix du niveau avec le meilleur ratio (0–5)
    tom_level = 0
    best_ratio = -1.0
    for level in range(0, 6):
        if tom_max[level] == 0:
            continue
        ratio = tom_scores[level] / tom_max[level]
        if ratio > best_ratio:
            best_ratio = ratio
            tom_level = level

    return domain_scores, domain_max, total_score, total_max, tom_level


# ==============================
# SEND EMAIL (TLS 587)
# ==============================

def send_email(code, age_group, domain_scores, domain_max, total_score, total_max, tom_level):
    subject = f"[Compétences sociales] Résultat - Code {code}"

    lines = [
        f"Code : {code}",
        f"Profil : {age_group}",
        f"Date : {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "Scores par domaine :",
    ]
    for d in DOMAINS:
        lines.append(f"- {d}: {domain_scores[d]} / {domain_max[d]}")
    lines += [
        "",
        f"Score total : {total_score} / {total_max}",
        f"Niveau de théorie de l'esprit (0–5) : {tom_level}",
        "",
        "Consultez l'app en mode praticien avec ce code."
    ]

    body = "\n".join(lines)
    message = f"Subject: {subject}\nFrom: {EMAIL_SENDER}\nTo: {PRACTITIONER_EMAIL}\n\n{body}"

    context = ssl.create_default_context()

    try:
        with smtplib.SMTP(EMAIL_HOST, EMAIL_PORT) as server:
            if USE_TLS:
                server.starttls(context=context)
            server.login(EMAIL_SENDER, EMAIL_APP_PASSWORD)
            server.sendmail(EMAIL_SENDER, PRACTITIONER_EMAIL, message.encode("utf-8"))
    except Exception as e:
        st.error(f"Erreur lors de l’envoi du mail : {e}")


# ==============================
# INTERFACE
# ==============================

st.set_page_config(page_title="Compétences sociales", page_icon="🧠")

st.title("🧠 Questionnaire de compétences sociales")
st.caption("Version adolescents / adultes – Passation anonyme")

mode = st.sidebar.radio("Mode", ["Passer le questionnaire", "Accès praticien"])


# --------------------------------------
# MODE PASSATION
# --------------------------------------

if mode == "Passer le questionnaire":

    age_group = "Profil non précisé"

    st.write("Pour chaque phrase, choisis la réponse qui te correspond le mieux :")
    st.write("0 = jamais · 1 = parfois · 2 = souvent · 3 = toujours")

    responses = {}

    # Affichage sans catégories
    for item in ITEMS:
        responses[item["id"]] = st.radio(
            f"{item['id']}. {item['label']}",
            [0, 1, 2, 3],
            index=1,
            horizontal=True,
            help=item["help"],
            key=f"q{item['id']}"
        )

    if st.button("Envoyer le questionnaire", type="primary"):

        domain_scores, domain_max, total_score, total_max, tom_level = compute_scores(responses)

        data = load_data()
        code = "CS-" + secrets.token_hex(3).upper()
        while code in data:
            code = "CS-" + secrets.token_hex(3).upper()

        data[code] = {
            "age_group": age_group,
            "responses": responses,
            "domain_scores": domain_scores,
            "domain_max": domain_max,
            "total_score": total_score,
            "total_max": total_max,
            "tom_level": tom_level,
            "timestamp": datetime.now().isoformat(),
        }
        save_data(data)

        send_email(code, age_group, domain_scores, domain_max, total_score, total_max, tom_level)

        st.success("Merci, ton questionnaire a été enregistré.")
        st.info("Un code a été envoyé au praticien.")


# --------------------------------------
# MODE PRATICIEN
# --------------------------------------

else:
    st.header("Accès praticien")
    code_input = st.text_input("Code de résultat")

    if st.button("Afficher les résultats"):

        data = load_data()
        code = code_input.strip()

        if code in data:
            result = data[code]

            st.success(f"Résultats pour le code : {code}")
            st.write(f"Profil : {result['age_group']}")
            st.write(f"Date : {result['timestamp']}")

            st.subheader("Scores par domaine")
            for d in DOMAINS:
                st.write(f"- {d}: {result['domain_scores'][d]} / {result['domain_max'][d]}")

            st.subheader("Score total")
            st.write(f"{result['total_score']} / {result['total_max']}")

            st.subheader("Niveau de théorie de l'esprit (0–5)")
            st.write(result["tom_level"])

            st.subheader("Détail des réponses")
            for item in ITEMS:
                qid = item["id"]
                # compatibilité str / int pour les anciennes données
                val = result["responses"].get(str(qid), result["responses"].get(qid, 0))
                st.write(f"{qid}. {item['label']} → {val}/3")
        else:
            st.error("Code introuvable.")
