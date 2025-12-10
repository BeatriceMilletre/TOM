    st.markdown("**Pour chaque phrase, choisis la réponse qui te correspond le mieux :**")
    st.markdown("0 = jamais · 1 = parfois · 2 = souvent · 3 = toujours")

    responses = {}

    # On ne montre plus les catégories, on affiche directement toutes les questions
    for item in ITEMS:
        key = f"q{item['id']}"
        val = st.radio(
            f"{item['id']}. {item['label']}",
            options=[0, 1, 2, 3],
            format_func=lambda x: {0: "0 – Jamais", 1: "1 – Parfois", 2: "2 – Souvent", 3: "3 – Toujours"}[x],
            index=1,  # par défaut "1 – Parfois" pour éviter le non-répondu
            key=key,
            help=item["help"],
        )
        responses[item["id"]] = val
