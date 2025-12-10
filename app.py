import streamlit as st
import json
import os
import secrets
import smtplib
import ssl
from datetime import datetime

# =========================================
# CONFIG EMAIL VIA SECRETS STREAMLIT
# =========================================

EMAIL_SENDER = st.secrets["EMAIL_SENDER"]
EMAIL_APP_PASSWORD = st.secrets["EMAIL_APP_PASSWORD"]
PRACTITIONER_EMAIL = st.secrets["PRACTITIONER_EMAIL"]


# =========================================
# FICHIERS DE DONNÉES
# =========================================

DATA_DIR = "data"
DATA_FILE = os.path.join(DATA_DIR, "social_comp_data.json")
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


# =========================================
# QUESTIONS (sans catégories visibles)
# Les domaines sont internes, invisibles au patient
# =========================================

QUESTIONS = [
    (1,  "Je comprends facilement l’émotion de quelqu’un.", "Compréhension sociale"),
    (2,  "Je repère quand quelqu’un veut changer de sujet.", "Compréhension sociale"),
    (3,  "Je comprends si quelqu’un plaisante ou est sérieux.", "Compréhension sociale"),
    (4,  "Je remarque quand quelqu’un n’est pas honnête ou exagère.", "Compréhension sociale"),
    (5,  "Je comprends l’intention derrière les paroles.", "Compréhension sociale"),
    (6,  "Je peux deviner ce qu’une personne pense dans une situation donnée.", "Compréhension sociale"),
    (7,  "Je comprends ce qu’on attend de moi dans un groupe.", "Compréhension sociale"),

    (8,  "J’arrive à entrer dans une conversation sans interrompre.", "Communication"),
    (9,  "Je sais terminer une conversation sans être brusque.", "Communication"),
    (10, "Je ne parle pas trop longtemps du même sujet.", "Communication"),
    (11, "Je m’adapte à la personne à qui je parle.", "Communication"),
    (12, "Je sais quand parler et quand écouter.", "Communication"),
    (13, "Je pose des questions pour faire avancer la conversation.", "Communication"),
    (14, "Je résume ce que l’autre dit pour vérifier ma compréhension.", "Communication"),
    (15, "Je repère quand un sujet met quelqu’un mal à l’aise.", "Communication"),

    (16, "Je garde mon calme dans les situations sociales compliquées.", "Régulation"),
    (17, "Je peux demander une pause quand je suis stressé.", "Régulation"),
    (18, "Je ne m’énerve pas trop vite quand on me contredit.", "Régulation"),
    (19, "Je sais comment me calmer après un conflit.", "Régulation"),
    (20, "Je gère bien les critiques, même injustes.", "Régulation"),
    (21, "Je peux dire « non » sans agressivité ni excès de gentillesse.", "Régulation"),

    (22, "Je peux changer de plan si nécessaire.", "Flexibilité"),
    (23, "J’accepte qu’on ne fasse pas comme je pensais.", "Flexibilité"),
    (24, "Je comprends le point de vue des autres.", "Flexibilité"),
    (25, "Je m’adapte à un nouveau groupe.", "Flexibilité"),
    (26, "J’accepte qu’on change de sujet même si je n’avais pas terminé.", "Flexibilité"),

    (27, "Je comprends la dynamique des groupes.", "Spécifique"),
    (28, "Je repère la moquerie gentille versus méchante.", "Spécifique"),
    (29, "Je reconnais une relation saine d’une relation toxique.", "Spécifique"),
    (30, "Je sais me défendre sans agresser.", "Spécifique"),
    (31, "Je sais proposer une activité ou un projet.", "Spécifique"),
    (32, "Je sais réparer un malentendu.", "Spécifique"),
    (33, "Je m’intègre sans être intrusif.", "Spécifique"),

    (34, "Je demande de l’aide quand j’en ai besoin.", "Autonomie"),
    (35, "J’exprime mes émotions sans envahir l’autre.", "Autonomie"),
    (36, "Je gère une situation imprévue.", "Autonomie"),
    (37, "Je parle à un adulte / professionnel sans stress excessif.", "Autonomie"),
    (38, "J’envoie des messages appropriés selon le contexte.", "Autonomie"),
    (39, "Je sais refuser quelque chose sans culpabiliser.", "Autonomie"),
]


# =========================================
# ToM mapping
# =========================================

TOM_LEVEL = {
    1:0, 2:1, 3:4, 4:3, 5:1, 6:2, 7:3,
    8:1, 9:1, 10:1, 11:2, 12:2, 13:2, 14:3, 15:4,
    16:0, 17:0, 18:2, 19:2, 20:3, 21:3,
    22:1, 23:1, 24:2, 25:3, 26:3,
    27:3, 28:4, 29:4, 30:2, 31:1, 32:4, 33:3,
    34:1, 35:2, 36:2, 37:3, 38:3, 39:4
}


# =========================================
# SCORE
# =========================================

def compute_scores(responses):
    domain_scores = {}
    domain_max = {}

    for qid, answer in responses.items():
        _, _, dom = next(q for q in QUESTIONS if q[0] == qid)
        domain_scores.setdefault(dom, 0)
        domain_scores[dom] += answer
        domain_max.setdefault(dom, 0)
        domain_max[dom] += 3

    total = sum(responses.values())
    total_max = len(QUESTIONS) * 3

    # ToM
    tom_scores = {i:0 for i in range(6)}
    tom_max = {i:0 for i in range(6)}

    for qid, val in responses.items():
        lvl = TOM_LEVEL.get(qid)
        tom_scores[lvl] += val
        tom_max[lvl] += 3

    tom_global = 0
    for lvl in range(6):
        if tom_max[lvl] > 0 and tom_scores[lvl] / tom_max[lvl] >= 0.6:
            tom_global = lvl

    return domain_scores, domain_max, total, total_max, tom_global


# =========================================
# EMAIL
# =========================================

def send_email(code, domain_scores, domain_max, total, total_max, tom_level):
    subject = f"[Compétences sociales] Nouveau résultat - Code {code}"

    lines = [
        f"Code : {code}",
        f"Date : {datetime.now()}",
        "",
        "Scores par domaine :",
    ]

    for dom in domain_scores:
        lines.append(f"- {dom} : {domain_scores[dom]} / {domain_max[dom]}")

    lines.append("")
    lines.append(f"Score total : {total} / {total_max}")
    lines.append(f"Niveau de ToM estimé : {tom_level}")

    body = "\n".join(lines)
    msg = f"Subject: {subject}\nFrom: {EMAIL_SENDER}\nTo: {PRACTITIONER_EMAIL}\n\n{body}"

    try:
        ctx = ssl.create_default_context()
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ctx) as server:
            server.login(EMAIL_SENDER, EMAIL_APP_PASSWORD)
            server.sendmail(EMAIL_SENDER, PRACTITIONER_EMAIL, msg.encode("utf-8"))
    except Exception as e:
        st.error(f"Erreur lors de l'envoi de l'email : {e}")


# =========================================
# UI STREAMLIT
# =========================================

st.title("🧠 Questionnaire de compétences sociales")
st.caption("Passation anonyme — 39 questions")

mode = st.sidebar.radio("Mode :", ["Passer le questionnaire", "Accès praticien"])


# =========================================
# MODE PATIENT : PASSATION
# =========================================

if mode == "Passer le questionnaire":

    st.write("Réponds à chaque affirmation en choisissant ce qui te correspond le mieux :")
    st.write("0 = jamais · 1 = parfois · 2 = souvent · 3 = toujours")
    st.write("---")

    responses = {}

    for qid, label, _ in QUESTIONS:
        responses[qid] = st.radio(
            f"{qid}. {label}",
            [0,1,2,3],
            horizontal=True,
            key=f"q_{qid}",
            index=1  # valeur par défaut = "parfois"
        )

    if st.button("Envoyer le questionnaire", type="primary"):

        # scores
        dom_scores, dom_max, total, total_max, tom = compute_scores(responses)

        # code
        data = load_data()
        code = "CS-" + secrets.token_hex(3).upper()
        data[code] = {
            "responses": responses,
            "domain_scores": dom_scores,
            "domain_max": dom_max,
            "total": total,
            "total_max": total_max,
            "tom_level": tom,
            "timestamp": str(datetime.now()),
        }
        save_data(data)

        # envoi email
        send_email(code, dom_scores, dom_max, total, total_max, tom)

        st.success("Merci, ton questionnaire a été enregistré.")
        st.info("Un code anonyme a été envoyé au praticien.")

# =========================================
# MODE PRATICIEN
# =========================================

elif mode == "Accès praticien":

    code = st.text_input("Code de résultat :")

    if st.button("Afficher les résultats"):

        data = load_data()
        if code in data:

            result = data[code]
            st.success(f"Résultats pour : {code}")

            st.write(f"Date : {result['timestamp']}")
            st.write(f"Score total : {result['total']} / {result['total_max']}")
            st.write(f"Niveau de ToM estimé : {result['tom_level']}")

            st.write("---")
            st.write("### Scores par domaine")
            for d in result["domain_scores"]:
                st.write(f"- {d} : {result['domain_scores'][d]} / {result['domain_max'][d]}")

            st.write("---")
            st.write("### Réponses détaillées")
            for qid, label, dom in QUESTIONS:
                st.write(f"{qid}. {label} → {result['responses'][qid]}/3  ({dom})")

        else:
            st.error("Code introuvable.")
