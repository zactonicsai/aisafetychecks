# make_data.py  -- builds train.jsonl (for studying) and test.jsonl (the pop quiz)
import json, random
random.seed(7)

SYSTEM = "You are the Sunny Market grocery helper. Answer in one short sentence."

AISLES = {
    "Aisle 1": ["apples", "bananas", "grapes", "strawberries", "carrots",
                "lettuce", "tomatoes", "onions", "potatoes", "broccoli"],
    "Aisle 2": ["milk", "cheese", "yogurt", "butter", "eggs", "orange juice"],
    "Aisle 3": ["bread", "bagels", "tortillas", "muffins"],
    "Aisle 4": ["peanut butter", "jam", "honey", "cereal", "oatmeal"],
    "Aisle 5": ["rice", "pasta", "canned beans", "tomato sauce", "soup", "flour", "sugar"],
    "Aisle 6": ["chips", "pretzels", "popcorn", "cookies", "crackers", "granola bars"],
    "Aisle 7": ["frozen pizza", "ice cream", "frozen vegetables", "frozen waffles"],
    "Aisle 8": ["paper towels", "dish soap", "trash bags", "laundry detergent", "sponges"],
    "Aisle 9": ["shampoo", "toothpaste", "bandages", "sunscreen"],
    "Aisle 10": ["pencils", "notebooks", "glue sticks", "markers", "backpacks"],
}

# 5 ways of asking that the model STUDIES...
TRAIN_QUESTIONS = [
    "Where do I find {item}?",
    "Which aisle has {item}?",
    "I'm looking for {item}.",
    "Can you help me find {item}?",
    "where's the {item}",
]
# ...and 1 way it has NEVER seen, used only on the quiz.
TEST_QUESTION = "Do you know where I can get {item}?"

# Things the store does not sell -> the model must learn to say so.
NOT_SOLD = ["tennis rackets", "car batteries", "puppies", "couches"]

# Store rules. Three phrasings for studying, one new phrasing for the quiz.
POLICY = [
    (["What time do you open?", "When does the store open?", "How early can I shop?"],
     "Are you open early in the morning?",
     "Sunny Market opens at 7 AM every day."),
    (["What time do you close?", "When does the store close?", "How late are you open?"],
     "Are you open late at night?",
     "Sunny Market closes at 10 PM every day."),
    (["Can I return something?", "What is your return policy?", "I need to return an item."],
     "How do refunds work?",
     "Bring your receipt within 30 days for a full refund at the front desk."),
    (["Where is the bathroom?", "Where are the restrooms?", "I need to use the restroom."],
     "Is there a bathroom here?",
     "The restrooms are at the back of the store next to the pharmacy."),
    (["Do you sell birthday cakes?", "Can I order a cake?", "Where can I get a cake for a party?"],
     "I want to buy a birthday cake.",
     "The bakery counter near Aisle 3 takes cake orders."),
    (["Do you have carts?", "Where are the shopping carts?", "Can I get a cart?"],
     "Where do I grab a cart?",
     "Shopping carts are just inside the front entrance."),
]

def row(user, assistant):
    return {"messages": [
        {"role": "system", "content": SYSTEM},
        {"role": "user", "content": user},
        {"role": "assistant", "content": assistant},
    ]}

train, test = [], []

for aisle, items in AISLES.items():
    for item in items:
        answer = f"You can find {item} in {aisle}."
        for q in TRAIN_QUESTIONS:
            train.append(row(q.format(item=item), answer))
        test.append(row(TEST_QUESTION.format(item=item), answer))

for item in NOT_SOLD:
    answer = f"Sorry, Sunny Market does not sell {item}."
    for q in TRAIN_QUESTIONS:
        train.append(row(q.format(item=item), answer))
    test.append(row(TEST_QUESTION.format(item=item), answer))

for study_qs, quiz_q, answer in POLICY:
    for q in study_qs:
        train.append(row(q, answer))
    test.append(row(quiz_q, answer))

random.shuffle(train)

with open("train.jsonl", "w") as f:
    for r in train:
        f.write(json.dumps(r) + "\n")
with open("test.jsonl", "w") as f:
    for r in test:
        f.write(json.dumps(r) + "\n")

print(f"Wrote {len(train)} study examples to train.jsonl")
print(f"Wrote {len(test)} quiz questions to test.jsonl")