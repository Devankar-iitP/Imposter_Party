import json, random

with open('words.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

random_word_object = random.choice(data["words"])
random_word = random_word_object["word"]
random_hint = random.choice(random_word_object["hints"])