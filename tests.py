# Tests for the Smart Fitness Session Analyzer.
#
# Run from the repository folder with:
#   python3 -m unittest tests.py     (Windows: python -m unittest tests.py)

import unittest

from data_generator import generate_fitness_data
from main import (Observation, Participant, RecoveryRules, SessionRules,
                  TrainingSession, analyse_session, build_session,
                  calculate_summary, check_value, create_report,
                  percent_difference)
from sample_data import get_all_scenarios


# Helper function: make_window
# What it does: makes one valid observation dictionary, so each test only has
#               to change the values it cares about.
# Input:  timestamp, heart_rate, activity and (optional) signal quality
# Output: a dictionary with one window of measurements
def make_window(timestamp, heart_rate, activity, quality=0.95):
    return {"timestamp": timestamp, "heart_rate": heart_rate, "skin_response": 1.5,
            "temperature": 32.5, "activity_level": activity, "signal_quality": quality}


# Helper function: make_session
# What it does: makes a session for a participant with a resting heart rate of 70.
# Input:  a list of observation dictionaries
# Output: a TrainingSession object
def make_session(windows):
    session = TrainingSession("test", Participant("T001", 70, 1.5, 32.5))
    for window in windows:
        session.add_observation(window)
    return session


# Tests for the standalone functions
class TestFunctions(unittest.TestCase):

    def test_check_value_accepts_good_value(self):
        self.assertIsNone(check_value("heart_rate", 80))

    def test_check_value_finds_problems(self):
        self.assertIn("missing", check_value("heart_rate", None))
        self.assertIn("outside", check_value("heart_rate", 265))
        self.assertIn("outside", check_value("activity_level", -0.2))
        self.assertIn("not a number", check_value("heart_rate", "fast"))
        self.assertIn("not a number", check_value("heart_rate", True))

    def test_calculate_summary(self):
        summary = calculate_summary([60, 70, 80])
        self.assertEqual(summary["average"], 70)
        self.assertEqual(summary["minimum"], 60)
        self.assertEqual(summary["maximum"], 80)

    def test_calculate_summary_empty_list(self):
        self.assertIsNone(calculate_summary([])["average"])

    def test_percent_difference(self):
        self.assertEqual(percent_difference(105, 70), 50.0)


# Tests for the Participant class (encapsulation)
class TestParticipant(unittest.TestCase):

    def test_impossible_resting_heart_rate_is_refused(self):
        with self.assertRaises(ValueError):
            Participant("P1", 300, 1.5, 32.5)

    def test_setter_keeps_old_value_when_new_value_is_wrong(self):
        participant = Participant("P1", 70, 1.5, 32.5)
        with self.assertRaises(ValueError):
            participant.resting_heart_rate = -5
        self.assertEqual(participant.resting_heart_rate, 70)

    def test_empty_id_is_refused(self):
        with self.assertRaises(ValueError):
            Participant("", 70, 1.5, 32.5)

    def test_from_profile_with_missing_value(self):
        with self.assertRaises(ValueError):
            Participant.from_profile({"participant_id": "P1"})


# Tests for the Observation class (validation)
class TestObservation(unittest.TestCase):

    def test_good_window_is_usable(self):
        self.assertTrue(Observation(make_window(0, 80, 0.2)).is_usable())

    def test_missing_key_is_rejected(self):
        window = make_window(0, 80, 0.2)
        del window["heart_rate"]
        observation = Observation(window)
        self.assertFalse(observation.is_usable())
        self.assertEqual(len(observation.errors), 1)

    def test_low_signal_is_flagged_not_rejected(self):
        observation = Observation(make_window(0, 80, 0.2, quality=0.4))
        self.assertFalse(observation.is_usable())
        self.assertEqual(len(observation.errors), 0)
        self.assertEqual(len(observation.warnings), 1)

    def test_bad_timestamp_is_rejected(self):
        self.assertFalse(Observation(make_window(-1, 80, 0.2)).is_usable())
        self.assertFalse(Observation(make_window(None, 80, 0.2)).is_usable())


# Tests for the classification rules
class TestClassification(unittest.TestCase):

    # The five generator scenarios are tested with 30 different seeds to show
    # that the rules do not only work for one lucky data set.
    def test_generator_scenarios_with_many_seeds(self):
        expected = {
            "resting": "resting",
            "moderate_activity": "moderate activity",
            "high_activity": "high activity",
            "recovery": "recovering",
            "poor_quality": "insufficient data",
        }
        for scenario, label in expected.items():
            for seed in range(30):
                profile, observations = generate_fitness_data(
                    scenario=scenario, seed=seed, number_of_windows=12)
                session = build_session(scenario, profile, observations)
                result = analyse_session(session, RecoveryRules())
                self.assertEqual(result["classification"], label,
                                 scenario + " failed with seed " + str(seed))

    def test_overriding_changes_the_result(self):
        # Starts hard and ends calm. The parent class only looks at averages,
        # the child class also looks at the trend.
        heart_rates = [140, 138, 135, 130, 115, 105, 95, 90, 82, 78, 76, 75]
        activities = [0.9, 0.9, 0.85, 0.8, 0.6, 0.5, 0.4, 0.35, 0.2, 0.15, 0.1, 0.1]
        windows = []
        for i in range(12):
            windows.append(make_window(i, heart_rates[i], activities[i]))
        session = make_session(windows)

        parent_label, _ = SessionRules().classify(session)
        child_label, _ = RecoveryRules().classify(session)
        self.assertNotEqual(parent_label, "recovering")
        self.assertEqual(child_label, "recovering")

    def test_too_few_windows_gives_insufficient_data(self):
        session = make_session([make_window(0, 75, 0.1), make_window(1, 76, 0.1)])
        label, _ = RecoveryRules().classify(session)
        self.assertEqual(label, "insufficient data")

    def test_has_enough_data(self):
        self.assertTrue(SessionRules.has_enough_data(8, 10))
        self.assertFalse(SessionRules.has_enough_data(3, 10))
        self.assertFalse(SessionRules.has_enough_data(0, 0))


# Tests for the result dictionary and the report
class TestResult(unittest.TestCase):

    def test_result_counts_for_mixed_session(self):
        name, profile, observations = get_all_scenarios()[5]   # unusual_some_bad_windows
        result = analyse_session(build_session(name, profile, observations), RecoveryRules())
        self.assertIsInstance(result, dict)
        self.assertEqual(result["total_windows"], 10)
        self.assertEqual(result["usable_windows"], 7)
        self.assertEqual(result["rejected_windows"], 2)
        self.assertEqual(result["flagged_windows"], 1)
        self.assertEqual(result["classification"], "moderate activity")

    def test_report_shows_the_result(self):
        name, profile, observations = get_all_scenarios()[0]   # resting
        result = analyse_session(build_session(name, profile, observations), RecoveryRules())
        self.assertIn("RESTING", create_report(result))

    def test_at_least_five_scenarios(self):
        self.assertGreaterEqual(len(get_all_scenarios()), 5)


if __name__ == "__main__":
    unittest.main()
