# Goal: create a script that generates N random words where N is the number provided by args
import random
import argparse
from wordfreq import top_n_list

def should_keep_word(word: str) -> bool:
    return len(word) > 1 or word == "a" or word == "i"


def get_words(n: int) -> list[str]:
    return [word for word in top_n_list("en", n) if should_keep_word(word)]


def random_words(quantity: int) -> list[str]:
    words = get_words(1000)
    wordlist: list[str] = []
    for i in range(quantity):
        wordlist.append(random.choice(words))
    return wordlist


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("n", type=int)
    args = parser.parse_args()

    words_concat = " ".join(random_words(args.n))
    
    print(words_concat)

if __name__ == "__main__":
    main()
