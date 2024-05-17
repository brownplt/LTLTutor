from transformers import GPT2LMHeadModel, GPT2Tokenizer

# Initialize the language model
def initialize_model():
    model_name = 'gpt2'
    model = GPT2LMHeadModel.from_pretrained(model_name)
    tokenizer = GPT2Tokenizer.from_pretrained(model_name)
    return model, tokenizer


model, tokenizer = initialize_model()


# Generate text using the language model
def generate_text(model, tokenizer, prompt):
    inputs = tokenizer.encode(prompt, return_tensors='pt')
    outputs = model.generate(inputs, max_length=50, num_return_sequences=1)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)


def ltl_to_english_sentence(ltl_formula):
    english_phrases = ltl_formula.__to_english__()
    prompt = english_phrases
    english_sentence = generate_text(model, tokenizer, prompt)
    return english_sentence
