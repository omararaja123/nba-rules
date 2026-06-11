"""
Generate 50 additional test questions for validation
Different phrasings and angles to test robustness
"""

import json

# Additional questions covering all 14 rules with different phrasings
additional_questions = [
    # Rule 1 - Court Dimensions (5 questions)
    {"id": 101, "rule": 1, "question": "How long is the NBA court?"},
    {"id": 102, "rule": 1, "question": "What is the free throw line distance from the basket?"},
    {"id": 103, "rule": 1, "question": "How far is the three-point line from the basket?"},
    {"id": 104, "rule": 1, "question": "What are the dimensions of the restricted area?"},
    {"id": 105, "rule": 1, "question": "How wide is the lane in basketball?"},

    # Rule 2 - Officials (5 questions)
    {"id": 106, "rule": 2, "question": "How many referees are on an NBA court?"},
    {"id": 107, "rule": 2, "question": "What does a crew chief do in basketball?"},
    {"id": 108, "rule": 2, "question": "Who controls the game clock?"},
    {"id": 109, "rule": 2, "question": "Can officials reverse their decisions?"},
    {"id": 110, "rule": 2, "question": "What is the replay official responsible for?"},

    # Rule 3 - Players (5 questions)
    {"id": 111, "rule": 3, "question": "How many players can a team have on the bench?"},
    {"id": 112, "rule": 3, "question": "How many players start a game?"},
    {"id": 113, "rule": 3, "question": "Who is the captain of a basketball team?"},
    {"id": 114, "rule": 3, "question": "What happens if a player leaves the bench?"},
    {"id": 115, "rule": 3, "question": "Can a coach be ejected from the game?"},

    # Rule 4 - Definitions (8 questions)
    {"id": 116, "rule": 4, "question": "What is the gather in basketball?"},
    {"id": 117, "rule": 4, "question": "How many steps can you take while dribbling?"},
    {"id": 118, "rule": 4, "question": "What is the definition of a dribble?"},
    {"id": 119, "rule": 4, "question": "Can you shoot after traveling?"},
    {"id": 120, "rule": 4, "question": "What is a pivot foot?"},
    {"id": 121, "rule": 4, "question": "When does traveling occur?"},
    {"id": 122, "rule": 4, "question": "Can you step with both feet?"},
    {"id": 123, "rule": 4, "question": "What is a step-back in basketball?"},

    # Rule 5 - Scoring (5 questions)
    {"id": 124, "rule": 5, "question": "How many points is a three-pointer?"},
    {"id": 125, "rule": 5, "question": "How many points is a free throw?"},
    {"id": 126, "rule": 5, "question": "When is a field goal counted?"},
    {"id": 127, "rule": 5, "question": "What happens if a ball is shot after the buzzer?"},
    {"id": 128, "rule": 5, "question": "Can you shoot across half-court at the end of a quarter?"},

    # Rule 6 - Putting Ball in Play (8 questions)
    {"id": 129, "rule": 6, "question": "How do you start a game in basketball?"},
    {"id": 130, "rule": 6, "question": "Who gets the ball at the start of the second quarter?"},
    {"id": 131, "rule": 6, "question": "Where is the jump ball conducted?"},
    {"id": 132, "rule": 6, "question": "What happens during a jump ball?"},
    {"id": 133, "rule": 6, "question": "Can a player jump twice during a jump ball?"},
    {"id": 134, "rule": 6, "question": "When is the ball live during a jump ball?"},
    {"id": 135, "rule": 6, "question": "Who can participate in a jump ball?"},
    {"id": 136, "rule": 6, "question": "What is the penalty for tipping before the ball reaches its peak?"},

    # Rule 7 - Shot Clock (8 questions)
    {"id": 137, "rule": 7, "question": "When does the 24-second clock reset?"},
    {"id": 138, "rule": 7, "question": "What is a 14-second reset in basketball?"},
    {"id": 139, "rule": 7, "question": "What happens when the shot clock expires?"},
    {"id": 140, "rule": 7, "question": "Does the shot clock reset on a foul?"},
    {"id": 141, "rule": 7, "question": "When does the shot clock stop?"},
    {"id": 142, "rule": 7, "question": "Can you play defense while the shot clock runs?"},
    {"id": 143, "rule": 7, "question": "What is the shot clock violation penalty?"},
    {"id": 144, "rule": 7, "question": "Does the clock stop at the end of a quarter?"},

    # Rule 8 - Out of Bounds (4 questions)
    {"id": 145, "rule": 8, "question": "What determines if a player is out of bounds?"},
    {"id": 146, "rule": 8, "question": "Can you throw the ball from out of bounds?"},
    {"id": 147, "rule": 8, "question": "How long do you have to throw in the ball?"},
    {"id": 148, "rule": 8, "question": "Can you bounce the ball on a throw-in?"},

    # Rule 9 - Free Throws (3 questions)
    {"id": 149, "rule": 9, "question": "Where does a player stand to take a free throw?"},
    {"id": 150, "rule": 9, "question": "What happens if the ball bounces out during a free throw?"},
    {"id": 151, "rule": 9, "question": "Can a defender interfere with a free throw?"},
]

print(f"Generated {len(additional_questions)} additional questions")
print()

# Save to file
output = {
    "version": "1.0",
    "type": "additional_test_questions",
    "count": len(additional_questions),
    "questions": additional_questions
}

with open('data/50_additional_test_questions.json', 'w') as f:
    json.dump(output, f, indent=2, ensure_ascii=False)

print(f"✅ Saved to data/50_additional_test_questions.json")
print()

# Show distribution
rule_dist = {}
for q in additional_questions:
    rule = q['rule']
    rule_dist[rule] = rule_dist.get(rule, 0) + 1

print("Distribution by rule:")
for rule in sorted(rule_dist.keys()):
    print(f"  Rule {rule:2d}: {rule_dist[rule]:2d} questions")

print()

