#!/usr/bin/env python3
"""Analyze city council survey responses for cost/budget mentions."""

# Survey responses from residents
responses = [
    "Great initiative but costs too much for small households.",
    "Love the idea, when does it start?",
    "The current bins are inconvenient, definitely support this change.",
    "We need more education before implementation, worried about cost.",
    "It's urgent, the ocean pollution is bad now.",
    "Supportive but concerned about budget."
]

# Keywords to search for (case-insensitive)
keywords = ['cost', 'budget', 'expense']

# Count responses mentioning any of the keywords
count = 0
matching_responses = []

for i, response in enumerate(responses, 1):
    response_lower = response.lower()
    if any(keyword in response_lower for keyword in keywords):
        count += 1
        matching_responses.append((i, response))

# Output results
print("=" * 60)
print("SURVEY RESPONSE ANALYSIS - City Council")
print("=" * 60)
print(f"\nTotal responses analyzed: {len(responses)}")
print(f"Responses mentioning 'cost', 'budget', or 'expense': {count}")
print(f"Percentage: {(count/len(responses))*100:.1f}%")

print("\n" + "-" * 60)
print("MATCHING RESPONSES:")
print("-" * 60)
for num, text in matching_responses:
    print(f"\n{num}. \"{text}\"")

print("\n" + "=" * 60)
print(f"TOTAL COUNT: {count}")
print("=" * 60)
