import itertools

survey_questions = {
    "upperorlower_sleepberth": ["upper", "lower"]
    "sleep_schedule": ["Early riser", "Night owl"],
    "study_preference": ["Silence", "Group study"],
    "noise_tolerance": ["Low", "Medium", "High"],
    "personality_type": ["Introvert", "Extrovert","ambivert"],
    "geographical_compatibility": ["Same area", "Doesn't matter"],
    "cle": ["Loudultural_preference": ["Same cultural/religious background", "Doesn't matter"],
    "food_preference": ["Same food mess", "Doesn't matter"],
    "academic_preference": ["Same course/class", "Doesn't matter"],
    "room_temperature_preference": ["Cold", "Hot"],
    "leisure_interests": ["Sports", "Gaming", "Movies", "Other hobbies"],
    "entertainment_sty", "Relaxed"],
}

def collect_user_data():
    print("Welcome to the Hostel Roommate Matchmaking System!")
    user_data = {}
    print("\nPlease answer the following questions:")
    
    for key, options in survey_questions.items():
        print(f"\n{key.replace('_', ' ').title()}:")
        for i, option in enumerate(options, 1):
            print(f"  {i}. {option}")
        choice = int(input(f"Select your choice (1-{len(options)}): "))
        user_data[key] = options[choice - 1]
    
    print("\nNow rank the importance of these preferences from 1 (most important) to 10 (least important):")
    preferences = list(survey_questions.keys())
    for i, pref in enumerate(preferences, 1):
        print(f"  {i}. {pref.replace('_', ' ').title()}")
    
    rankings = []
    for i in range(1, len(preferences) + 1):
        rank = int(input(f"Enter preference ranked {i}: ")) - 1
        rankings.append(preferences[rank])
    user_data["rankings"] = rankings
    
    return user_data


def calculate_score(user1, user2):
    score = 0
    for key in survey_questions.keys():
        if user1[key] == user2[key]:
            score += user1["rankings"].index(key) + 1
    return score


def match_users(users):
    matches = []
    for user1, user2 in itertools.combinations(users, 2):
        score = calculate_score(user1, user2)
        matches.append((user1["name"], user2["name"], score))
    matches.sort(key=lambda x: x[2], reverse=True)
    return matches


if __name__ == "__main__":
    users = []
    print("Enter data for 2 or more users.")
    
    while True:
        user = collect_user_data()
        user["name"] = input("\nEnter your name: ")
        users.append(user)
        
        more_users = input("Do you want to add another user? (yes/no): ").strip().lower()
        if more_users != "yes":
            break
    
    print("\nMatching roommates...")
    matched_pairs = match_users(users)
    
    print("\nTop Matches:")
    for user1, user2, score in matched_pairs:
        print(f"{user1} and {user2} with compatibility score: {score}")
