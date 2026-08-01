from word2number import w2n

def test():
    words = "ten meters".replace(",", "").replace(".", " . ").split()
    unit_map = {
        "meters": "m",
    }
    words = [unit_map.get(w.lower(), w) for w in words]
    
    processed_words = []
    current_number_words = []
    
    valid_number_words = {
        "zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine",
        "ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen",
        "eighteen", "nineteen", "twenty", "thirty", "forty", "fifty", "sixty", "seventy",
        "eighty", "ninety", "hundred", "thousand", "million", "billion", "point"
    }
    
    for word in words:
        if word.lower() in valid_number_words:
            current_number_words.append(word)
        else:
            if current_number_words:
                try:
                    num = w2n.word_to_num(" ".join(current_number_words))
                    processed_words.append(str(num))
                except ValueError:
                    processed_words.extend(current_number_words)
                current_number_words = []
            processed_words.append(word)
            
    if current_number_words:
        try:
            num = w2n.word_to_num(" ".join(current_number_words))
            processed_words.append(str(num))
        except ValueError:
            processed_words.extend(current_number_words)
            
    print(" ".join(processed_words).replace(" . ", "."))
    
test()
