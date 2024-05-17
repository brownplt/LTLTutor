# from transformers import pipeline
# import spacy

# nlp = spacy.load("en_core_web_sm")

# generator = pipeline('text-generation', model='distilgpt2')

# # Function to generate a grammatically correct sentence using a transformer model
# def generate_grammatically_correct_sentence(english_sentence):
#     prompt = f"Translate this logical expression to a grammatically correct English sentence: {english_sentence}."
#     result = generator(prompt, max_length=50, num_return_sequences=1)
#     return result[0]['generated_text']


# def ltl_to_english_sentence(ltl_formula):
#     print("Translating " + str(ltl_formula) + " to English")
#     english_phrases = ltl_formula.__to_english__()
#     prompt = english_phrases
#     print("Symbolic pass: " + prompt)

#     #english_sentence = generate_text(model, tokenizer, prompt)

#     doc = nlp(prompt)
#     corrected_sentence = ' '.join([token.text for token in doc])


#     print("After SpaCy pass (directly on symbolic): " + corrected_sentence)

#     y = generate_grammatically_correct_sentence(prompt)
#     print("After transformer pass (directly on symbolic): " + y)


#     return corrected_sentence


# from transformers import pipeline





