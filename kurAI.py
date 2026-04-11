import json
import os
import random
import markovify
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

DATA_FILE = "data.json"
MEMORY_FILE = "memory.json"
RESPONSES_FILE = "responses.txt"

def load_data():
    if not os.path.exists(DATA_FILE):
        return []
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    for item in data:
        item["responses"] = list(dict.fromkeys(item["responses"]))
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)


def load_memory():
    if not os.path.exists(MEMORY_FILE):
        return {}
    with open(MEMORY_FILE, "r") as f:
        return json.load(f)

def save_memory(memory):
    with open(MEMORY_FILE, "w") as f:
        json.dump(memory, f, indent=4)


def clean(text):
    return text.lower().strip()


def get_response(message, data):
    if not data:
        return None
    questions = [item["question"] for item in data]
    vectorizer = TfidfVectorizer()
    vectors = vectorizer.fit_transform(questions + [message])
    similarities = cosine_similarity(vectors[-1], vectors[:-1])[0]
    best_index = similarities.argmax()
    best_score = similarities[best_index]
    if best_score < 0.2:
        return None
    responses = data[best_index]["responses"]
    return random.choice(responses)


def markov_generate():
    if not os.path.exists(RESPONSES_FILE):
        return None
    with open(RESPONSES_FILE, "r") as f:
        text = f.read()
    if not text.strip():
        return None
    text_model = markovify.Text(text)
    sentence = text_model.make_sentence()
    return sentence

def add_to_responses(sentence):
    if os.path.exists(RESPONSES_FILE):
        with open(RESPONSES_FILE, "r") as f:
            lines = [line.strip() for line in f.readlines()]
        if sentence in lines:
            return
    with open(RESPONSES_FILE, "a") as f:
        f.write(sentence + "\n")

def main():
    print("KurAI (Version 1.0.0)")

    data = load_data()
    memory = load_memory()

    while True:
        os.system("clear")
        user_input = input("Toi: ")
        if user_input.lower() in ["quit", "bye"]:
            print("Bot: Au revoir ! 👋")
            break

        user_input_clean = clean(user_input)

        if "appelle-moi" in user_input_clean:
            name = user_input_clean.replace("appelle-moi", "").strip()
            memory["name"] = name
            save_memory(memory)
            print(f"Bot: D'accord, je t'appellerai {name}")
            continue

        response = get_response(user_input_clean, data)

        if not response:
            generated = markov_generate()
            if generated:
                response = generated
            else:
                response = "Oh le sang j'ai jamais appris à répondre à ça encore"

        if "name" in memory:
            response = response.replace("{name}", memory["name"])

        print("Bot:", response)

        print("Comment KurAI devrait répondre la prochaine fois ?")
        correction = input("Corriger/valider cette réponse ou ajouter une nouvelle réponse : ").strip()
        if correction:
            response = correction

        add_to_responses(response)
        found = False
        for item in data:
            if item["question"] == user_input_clean:
                if response not in item["responses"]:
                    item["responses"].append(response)
                found = True
                break
        if not found:
            data.append({"question": user_input_clean, "responses": [response]})
        save_data(data)

if __name__ == "__main__":
    main()