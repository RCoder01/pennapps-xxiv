import random

name = input("What is your name?\n")
print("Hello " + name + "!\n")

age = input("How old are you?\n")
if int(age) >= 21:
    print("Congratulations! You are " + str(age) + " years old and you can legally drink!\n")
else:
    print("Congratulations! You are " + str(age) + " years old and you can illegally drink!\n")

word = "REACT"
print("\nI am thinking of a 5 letter word and you have 6 chances to guess it. Make a guess and I will tell you X if the letter is wrong, R if the letter is right but in the wrong spot, and C if the letter is right and in the right spot.\n")
for i in range(6):
    wordset = set(word)
    guess = input("Guess #" + str(i+1) + "\n").upper()
    while len(guess) != 5:
        guess = input("Guess again.\n").upper()
    result = ""
    for i in range(len(guess)):
        if word[i] == guess[i]:
            wordset.remove(guess[i])
            result = result + "C"
        elif guess[i] in wordset:
            wordset.remove(guess[i])
            result = result + "R"        
        else:
            result = result + "X"
    print(result + "\n")
    if word == guess:
        print("Congratulations you won!")
        break


input("\nI am thinking of a number between 1-1000. Guess and I will say over or under.\n")

while True:
    rand = random.randint(0,1)
    if rand == 1:
        input("Too high. Guess again.\n")
    else:
        input("Too low. Guess again.\n")