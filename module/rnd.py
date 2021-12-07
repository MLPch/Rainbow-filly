import random


def key():
    key = str(random.randrange(1000000000, 9999999999, 1))
    return key


def choice(l):
    choice = random.choice(l)
    return choice


def time(mintime):
    maxtime = mintime * 3
    time = random.randrange(mintime, maxtime, 1)
    return time


if __name__ == "__main__":
    print(key())
