# Sample data for the Smart Fitness Session Analyzer.
#
# Five scenarios are made with the instructor's data generator
# (data_generator.py). Two extra scenarios are written by hand to test
# unusual cases that the generator does not create.

from data_generator import generate_fitness_data


# The five scenarios required by the assignment, with the seed used for each.
# A fixed seed means the program prints the same result every time it runs.
GENERATOR_SCENARIOS = [
    ("resting", 11),
    ("moderate_activity", 12),
    ("high_activity", 13),
    ("recovery", 14),
    ("poor_quality", 15),
]


# Unusual case 1: a moderate session where 3 of the 10 windows are bad.
# The program should skip the bad windows but still classify the session.
MIXED_PROFILE = {
    "participant_id": "P006",
    "baseline_heart_rate": 68,
    "baseline_skin_response": 1.6,
    "baseline_temperature": 32.3,
}

MIXED_OBSERVATIONS = [
    {"timestamp": 0, "heart_rate": 92, "skin_response": 1.9, "temperature": 32.5, "activity_level": 0.48, "signal_quality": 0.91},
    {"timestamp": 1, "heart_rate": 95, "skin_response": 2.0, "temperature": 32.6, "activity_level": 0.52, "signal_quality": 0.93},
    {"timestamp": 2, "heart_rate": None, "skin_response": 2.0, "temperature": 32.6, "activity_level": 0.50, "signal_quality": 0.90},
    {"timestamp": 3, "heart_rate": 97, "skin_response": 2.1, "temperature": 32.7, "activity_level": 0.55, "signal_quality": 0.88},
    {"timestamp": 4, "heart_rate": 94, "skin_response": 2.0, "temperature": 32.6, "activity_level": 0.49, "signal_quality": 0.35},
    {"timestamp": 5, "heart_rate": 96, "skin_response": 2.1, "temperature": 32.7, "activity_level": 0.53, "signal_quality": 0.92},
    {"timestamp": 6, "heart_rate": 93, "skin_response": 2.0, "temperature": 32.6, "activity_level": 1.40, "signal_quality": 0.94},
    {"timestamp": 7, "heart_rate": 95, "skin_response": 2.0, "temperature": 32.7, "activity_level": 0.51, "signal_quality": 0.90},
    {"timestamp": 8, "heart_rate": 94, "skin_response": 1.9, "temperature": 32.6, "activity_level": 0.50, "signal_quality": 0.89},
    {"timestamp": 9, "heart_rate": 92, "skin_response": 1.9, "temperature": 32.5, "activity_level": 0.47, "signal_quality": 0.93},
]


# Unusual case 2: a very short session with a text value and a missing key.
# Too few windows can be used, so the result should be "insufficient data".
SHORT_PROFILE = {
    "participant_id": "P007",
    "baseline_heart_rate": 65,
    "baseline_skin_response": 1.8,
    "baseline_temperature": 32.4,
}

SHORT_OBSERVATIONS = [
    {"timestamp": 0, "heart_rate": 70, "skin_response": 1.9, "temperature": 32.5, "activity_level": 0.10, "signal_quality": 0.95},
    {"timestamp": 1, "heart_rate": "fast", "skin_response": 1.9, "temperature": 32.5, "activity_level": 0.12, "signal_quality": 0.94},
    {"timestamp": 2, "skin_response": 2.0, "temperature": 32.6, "activity_level": 0.11, "signal_quality": 0.93},
]


# Function: get_all_scenarios
# What it does: collects every scenario the program should analyse.
# Input:  number_of_windows (how many windows the generator should make, default 12)
# Output: a list of tuples: (scenario name, profile dictionary, list of observation dictionaries)
def get_all_scenarios(number_of_windows=12):
    scenarios = []

    participant_number = 1
    for scenario_name, seed in GENERATOR_SCENARIOS:
        profile, observations = generate_fitness_data(
            participant_id="P00" + str(participant_number),
            scenario=scenario_name,
            seed=seed,
            number_of_windows=number_of_windows,
        )
        scenarios.append((scenario_name, profile, observations))
        participant_number = participant_number + 1

    scenarios.append(("unusual_some_bad_windows", MIXED_PROFILE, MIXED_OBSERVATIONS))
    scenarios.append(("unusual_short_session", SHORT_PROFILE, SHORT_OBSERVATIONS))
    return scenarios
