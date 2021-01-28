import markovify

with open("src/forums/ydrc.txt") as f:
    text = f.read()

text_model = markovify.NewlineText(text, state_size=4)

def get_responses(count):
    """Gets a specific number (equal to count) of generated markov strings."""
    sentences = 0
    while sentences < count:
        sentence = text_model.make_sentence()
        if sentence != None:
            return(sentence)
            sentences += 1