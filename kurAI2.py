import json
import os
import random
import wikipedia
import re

os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["TRANSFORMERS_VERBOSITY"] = "error"

from sentence_transformers import SentenceTransformer, util

DATA_FILE = "data.json"
MEMORY_FILE = "memory.json"

model = SentenceTransformer('all-MiniLM-L6-v2')

wikipedia.set_lang("fr")


# ------------------ DATA ------------------

def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        return json.load(f)


def save_data(data):
    for item in data:
        item["responses"] = list(dict.fromkeys(item["responses"]))

    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


# ------------------ MEMORY ------------------

def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {}
    with open(MEMORY_FILE, "r") as f:
        return json.load(f)


def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=4, ensure_ascii=False)


# ------------------ UTILS ------------------

def clean(text):
    return text.lower().strip()


def vary_response(response):
    variants = [
        response,
        response + " 😄",
        "Hmm... " + response,
        response.capitalize()
    ]
    return random.choice(variants)


def is_factual_question(text):
    keywords = [
        "qui", "quoi", "quand", "où", "ou", "pourquoi",
        "comment", "combien", "quel", "quelle"
    ]
    return any(word in text for word in keywords)


# ------------------ FORMAT WIKI ------------------

def clean_wiki(text):
    text = re.sub(r"\(.*?\)", "", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def format_response(text):
    text = clean_wiki(text)

    sentences = text.split(".")
    if len(sentences) > 2:
        text = ".".join(sentences[:2]) + "."

    starters = [
        "",
        "Alors, ",
        "Eh bien, ",
        "En gros, ",
        "Pour faire simple, "
    ]

    return random.choice(starters) + text.strip()


def humanize(text):
    replacements = {
        " est un": " c'est un",
        " est une": " c'est une",
        " né": " il est né",
        " née": " elle est née",
        " mort": " il est mort",
        " morte": " elle est morte"
    }

    for k, v in replacements.items():
        text = text.replace(k, v)

    return text


# ------------------ IA CORE ------------------

def get_response(message, data):
    if not data:
        return None

    # 🔥 1. MATCH EXACT AVANT EMBEDDINGS (IMPORTANT)
    for item in data:
        if item["question"] == message:
            return random.choice(item["responses"])

    # 🔥 2. SIMILARITÉ
    questions = [item["question"] for item in data]

    embeddings_questions = model.encode(questions, convert_to_tensor=True)
    embedding_input = model.encode(message, convert_to_tensor=True)

    similarities = util.cos_sim(embedding_input, embeddings_questions)[0]
    best_index = similarities.argmax().item()
    best_score = similarities[best_index].item()

    if best_score < 0.5:
        return None

    response = random.choice(data[best_index]["responses"])

    if is_factual_question(message):
        if "je sais pas" in response.lower():
            return None

    return response


# ------------------ WIKIPEDIA ------------------

def search_wikipedia(query):
    try:
        result = wikipedia.summary(query, sentences=3)
        return result
    except:
        return None


# ------------------ INTENTS ------------------

def detect_intent(text):
    if any(word in text for word in ["bonjour", "salut", "yo", "hello"]):
        return "greeting"
    if "ça va" in text or "ca va" in text:
        return "how_are_you"
    if "merci" in text:
        return "thanks"
    if "qui es-tu" in text:
        return "who"
    return "unknown"


# ------------------ MAIN ------------------

def main():
    print("KurAI (Version 3.3 🤖✨)")

    data = load_data()
    memory = load_memory()

    while True:
        user_input = input("Toi: ")

        if user_input.lower() in ["quit", "bye"]:
            print("Bot: Au revoir ! 👋")
            break

        user_input_clean = clean(user_input)

        # mémoire nom
        if "appelle-moi" in user_input_clean:
            name = user_input_clean.replace("appelle-moi", "").strip()
            memory["name"] = name
            save_memory(memory)
            print(f"Bot: D'accord, je t'appellerai {name} 😄")
            continue

        # intents
        intent = detect_intent(user_input_clean)

        if intent == "greeting":
            print("Bot: Salut 😄")
            continue
        elif intent == "how_are_you":
            print("Bot: Tranquille et toi ?")
            continue
        elif intent == "thanks":
            print("Bot: Avec plaisir 😄")
            continue
        elif intent == "who":
            print("Bot: Je suis KurAI, une IA en évolution 🔥")
            continue

        # IA locale
        response = get_response(user_input_clean, data)

        # 🌐 fallback Internet
        if not response:
            wiki_result = search_wikipedia(user_input_clean)

            if wiki_result:
                response = humanize(format_response(wiki_result))
            else:
                if is_factual_question(user_input_clean):
                    response = "Je ne sais pas encore, mais tu peux m'apprendre 😉"
                else:
                    response = "Je ne suis pas sûr de comprendre 🤔"

        # nom
        if "name" in memory:
            response = response.replace("{name}", memory["name"])

        response = vary_response(response)

        print("Bot:", response)

        # ------------------ TRAINING ------------------

        print("Améliorer la réponse ? (laisser vide pour skip)")
        correction = input(">> ").strip()

        if correction:
            if len(correction.split()) < 2:
                print("⚠️ Réponse ignorée (trop courte)")
                continue

            if "je sais pas" in correction.lower():
                print("⚠️ Réponse ignorée (trop générique)")
                continue

            if len(correction) > 300:
                print("⚠️ Réponse ignorée (trop longue)")
                continue

            found = False
            for item in data:
                if item["question"] == user_input_clean:
                    if correction not in item["responses"]:
                        item["responses"].append(correction)
                    found = True
                    break

            if not found:
                data.append({
                    "question": user_input_clean,
                    "responses": [correction]
                })

            # 🔥 SAUVEGARDE FORCÉE (IMPORTANT)
            save_data(data)


if __name__ == "__main__":
    main()