import json, random

with open('words.json', 'r', encoding='utf-8') as file:
    data = json.load(file)

def get_random_word():
    random_word_object = random.choice(data["words"])
    word = random_word_object["word"]
    hint = random.choice(random_word_object["hints"])
    
    return word, hint