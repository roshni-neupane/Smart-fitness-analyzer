# Smart Fitness Session Analyzer - Option A
# This program reads simulated measurements from a wearable device, checks
# which measurements can be trusted, compares them with the participant's
# resting values, and decides what kind of training session it was.
# Run it from the repository folder with: python3 main.py (or: python main.py)

import statistics

from sample_data import get_all_scenarios

# ---------------------------------------------------------------------------
# Settings (all rule values are kept here so they are easy to change)
# ---------------------------------------------------------------------------

# Lowest and highest value that is physically possible for each field
ALLOWED_RANGES = {
    "heart_rate": (30, 220),
    "skin_response": (0, 20),
    "temperature": (25, 42),
    "activity_level": (0, 1),
    "signal_quality": (0, 1),
}

# The four fields that describe the body / movement (signal_quality is not one)
MEASUREMENT_FIELDS = ["heart_rate", "skin_response", "temperature", "activity_level"]

LOWEST_GOOD_SIGNAL = 0.7        # windows below this are flagged as unreliable
MINIMUM_USABLE_WINDOWS = 4      # we need at least this many usable windows
MINIMUM_USABLE_PERCENT = 50     # and at least this share of all windows

RESTING_MAX_HR_PERCENT = 15     # resting: heart rate at most 15 % above baseline
RESTING_MAX_ACTIVITY = 0.30     #          and activity below 0.30
HIGH_MIN_HR_PERCENT = 65        # high: heart rate at least 65 % above baseline
HIGH_MIN_ACTIVITY = 0.67        #       or activity at least 0.67

WINDOWS_TO_COMPARE = 3          # recovery compares the first 3 and last 3 windows
RECOVERY_MIN_START_PERCENT = 25 # heart rate must start at least 25 % above baseline
RECOVERY_MIN_HR_DROP = 15       # heart rate must drop by at least 15 bpm
RECOVERY_MIN_ACTIVITY_DROP = 0.2  # activity must drop by at least 0.2


# ---------------------------------------------------------------------------
# Standalone functions
# ---------------------------------------------------------------------------

# Function: check_value
# What it does: checks one measurement and says what is wrong with it, if anything.
# Input:  field_name (text, e.g. "heart_rate") and value (the measured value)
# Output: None if the value is fine, otherwise a text describing the problem
def check_value(field_name, value):
    if value is None:
        return field_name + " is missing"

    # True/False count as numbers in Python, so they are rejected on purpose
    if type(value) not in (int, float):
        return field_name + " is not a number (" + str(value) + ")"

    lowest, highest = ALLOWED_RANGES[field_name]
    if value < lowest or value > highest:
        return (field_name + " = " + str(value) + " is outside the allowed range "
                + str(lowest) + " to " + str(highest))

    return None


# Function: calculate_summary
# What it does: calculates the average, lowest and highest value of a list.
# Input: numbers (a list of numbers)
# Output: a dictionary with average, minimum and maximum. All three values
#         are None if the list is empty.
def calculate_summary(numbers):
    if len(numbers) == 0:
        return {"average": None, "minimum": None, "maximum": None}

    return {
        "average": round(statistics.mean(numbers), 2),
        "minimum": min(numbers),
        "maximum": max(numbers),
    }


# Function: percent_difference
# What it does: says how many percent a value is above (or below) a reference.
# Input:  value (number) and reference (number, not zero)
# Output: a number, e.g. 50.0 means "50 % above the reference"
def percent_difference(value, reference):
    return round((value - reference) / reference * 100, 1)


# Function: average_of_field
# What it does: finds the average of one field in a list of observations.
# Input:  observations (a list of Observation objects) and field_name (text)
# Output: the average as a number
def average_of_field(observations, field_name):
    values = []
    for observation in observations:
        values.append(observation.get_value(field_name))
    return statistics.mean(values)


# Function: analyse_session
# What it does: runs the whole analysis for one session and collects every
#               result in one dictionary.
# Input:  session (a TrainingSession object) and rules (a SessionRules object
#         or any object that inherits from it)
# Output: a dictionary with counts, problems, summaries, comparison with the
#         reference values, the classification and the explanation
def analyse_session(session, rules):
    usable = session.get_usable_observations()

    rejected_count = 0
    flagged_count = 0
    problems = []
    for observation in session.observations:
        if len(observation.errors) > 0:
            rejected_count = rejected_count + 1
        elif len(observation.warnings) > 0:
            flagged_count = flagged_count + 1
        for problem in observation.errors + observation.warnings:
            problems.append("window " + str(observation.timestamp) + ": " + problem)

    label, explanation = rules.classify(session)

    result = {
        "scenario": session.name,
        "participant_id": session.participant.participant_id,
        "total_windows": len(session.observations),
        "usable_windows": len(usable),
        "rejected_windows": rejected_count,
        "flagged_windows": flagged_count,
        "problems": problems,
        "summaries": session.get_summaries(),
        "comparison": session.compare_with_reference(),
        "classification": label,
        "explanation": explanation,
    }
    return result


# Function: create_report
# What it does: turns the result dictionary into text that is easy to read.
# Input:  result (the dictionary returned by analyse_session)
# Output: one long text (string) that can be printed
def create_report(result):
    lines = []
    lines.append("=" * 60)
    lines.append("Scenario:    " + result["scenario"])
    lines.append("Participant: " + result["participant_id"])
    lines.append("Windows:     " + str(result["usable_windows"]) + " usable out of "
                 + str(result["total_windows"]) + " (" + str(result["rejected_windows"])
                 + " rejected, " + str(result["flagged_windows"]) + " flagged)")

    if len(result["problems"]) > 0:
        lines.append("Problems found:")
        for problem in result["problems"]:
            lines.append("  - " + problem)

    if len(result["summaries"]) > 0:
        lines.append("Measurements (usable windows only):")
        lines.append("  {:<16}{:>8}{:>8}{:>8}".format("field", "avg", "min", "max"))
        for field_name in MEASUREMENT_FIELDS:
            summary = result["summaries"][field_name]
            lines.append("  {:<16}{:>8}{:>8}{:>8}".format(
                field_name, summary["average"], summary["minimum"], summary["maximum"]))

        comparison = result["comparison"]
        lines.append("Compared with personal reference:")
        lines.append("  heart rate:    {:+.1f} bpm ({:+.1f} %)".format(
            comparison["heart_rate_difference"], comparison["heart_rate_percent"]))
        lines.append("  skin response: {:+.2f}".format(comparison["skin_response_difference"]))
        lines.append("  temperature:   {:+.2f} C".format(comparison["temperature_difference"]))

    lines.append("Result:      " + result["classification"].upper())
    lines.append("Why:         " + result["explanation"])
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Classes
# ---------------------------------------------------------------------------

# Class: Participant
# What it does: stores one participant and their personal reference (resting)
#               values. The resting heart rate is protected (_resting_heart_rate)
#               and can only be changed through a property that checks the value.
# Input:  participant_id (text), resting_heart_rate (bpm),
#         resting_skin_response (number), resting_temperature (degrees C)
# Output: a Participant object
class Participant:

    # Method: __init__ (constructor)
    # What it does: saves the participant's id and reference values.
    # Input:  the four values listed above
    # Output: nothing (raises ValueError if the id or a reference value is invalid)
    def __init__(self, participant_id, resting_heart_rate, resting_skin_response,
                 resting_temperature):
        if type(participant_id) != str or participant_id.strip() == "":
            raise ValueError("participant_id must be a non-empty text")

        for field_name, value in [("skin_response", resting_skin_response),
                                  ("temperature", resting_temperature)]:
            problem = check_value(field_name, value)
            if problem is not None:
                raise ValueError("Invalid reference value: " + problem)

        self.participant_id = participant_id
        self.resting_heart_rate = resting_heart_rate   # uses the property below
        self.resting_skin_response = resting_skin_response
        self.resting_temperature = resting_temperature

    # Property (getter): resting_heart_rate
    # What it does: gives back the protected resting heart rate.
    # Input:  nothing
    # Output: the resting heart rate (bpm)
    @property
    def resting_heart_rate(self):
        return self._resting_heart_rate

    # Property (setter): resting_heart_rate
    # What it does: changes the resting heart rate, but only if the new value
    #               is possible. This protects the value used in every comparison.
    # Input:  value (new resting heart rate)
    # Output: nothing (raises ValueError if the value is impossible)
    @resting_heart_rate.setter
    def resting_heart_rate(self, value):
        problem = check_value("heart_rate", value)
        if problem is not None:
            raise ValueError("Invalid resting heart rate: " + problem)
        self._resting_heart_rate = value

    # Class method: from_profile
    # What it does: creates a Participant from the profile dictionary that the
    #               data generator returns. Needed because the generator uses
    #               different key names (e.g. "baseline_heart_rate").
    # Input:  profile (a dictionary)
    # Output: a new Participant object
    @classmethod
    def from_profile(cls, profile):
        return cls(profile.get("participant_id"),
                   profile.get("baseline_heart_rate"),
                   profile.get("baseline_skin_response"),
                   profile.get("baseline_temperature"))


# Class: Observation
# What it does: stores one measurement window and checks it straight away.
#               Missing or impossible values go into "errors" (the window is
#               rejected). Low signal quality goes into "warnings" (the window
#               is flagged). Only windows without errors or warnings are used.
# Input:  a dictionary like {"timestamp": 2, "heart_rate": 118, ...}
# Output: an Observation object
class Observation:

    # Method: __init__ (constructor)
    # What it does: copies the values from the dictionary and validates them.
    # Input:  data (dictionary with one window of measurements)
    # Output: nothing
    def __init__(self, data):
        # .get() gives None when a key is missing, so the program does not crash
        self.timestamp = data.get("timestamp")
        self.values = {}
        for field_name in MEASUREMENT_FIELDS:
            self.values[field_name] = data.get(field_name)
        self.signal_quality = data.get("signal_quality")

        self.errors = []
        self.warnings = []
        self.validate()

    # Method: validate
    # What it does: checks the timestamp, every measurement and the signal quality.
    # Input:  nothing (uses the object's own values)
    # Output: nothing (fills self.errors and self.warnings)
    def validate(self):
        if type(self.timestamp) != int or self.timestamp < 0:
            self.errors.append("timestamp is not a whole number of 0 or more")

        for field_name in MEASUREMENT_FIELDS:
            problem = check_value(field_name, self.values[field_name])
            if problem is not None:
                self.errors.append(problem)

        problem = check_value("signal_quality", self.signal_quality)
        if problem is not None:
            self.errors.append(problem)
        elif self.signal_quality < LOWEST_GOOD_SIGNAL:
            self.warnings.append("low signal quality (" + str(self.signal_quality) + ")")

    # Method: is_usable
    # What it does: says whether this window can be used in the analysis.
    # Input:  nothing
    # Output: True or False
    def is_usable(self):
        return len(self.errors) == 0 and len(self.warnings) == 0

    # Method: get_value
    # What it does: gives back one measurement from this window.
    # Input:  field_name (text, e.g. "heart_rate")
    # Output: the value of that field
    def get_value(self, field_name):
        return self.values[field_name]


# Class: TrainingSession
# What it does: groups one participant and all their observation windows into
#               one session (composition: a session HAS a participant and HAS
#               a list of observations).
# Input:  name (text), participant (a Participant object)
# Output: a TrainingSession object
class TrainingSession:

    # Method: __init__ (constructor)
    # What it does: creates an empty session for one participant.
    # Input:  name (scenario name), participant (Participant object)
    # Output: nothing
    def __init__(self, name, participant):
        self.name = name
        self.participant = participant
        self.observations = []

    # Method: add_observation
    # What it does: turns one raw dictionary into an Observation and adds it.
    # Input:  data (dictionary with one window of measurements)
    # Output: nothing
    def add_observation(self, data):
        self.observations.append(Observation(data))

    # Method: get_usable_observations
    # What it does: finds the windows that passed validation, sorted by time
    #               (the order matters when looking for recovery).
    # Input:  nothing
    # Output: a list of Observation objects
    def get_usable_observations(self):
        usable = []
        for observation in self.observations:
            if observation.is_usable():
                usable.append(observation)
        usable.sort(key=lambda observation: observation.timestamp)
        return usable

    # Method: get_summaries
    # What it does: calculates average, minimum and maximum for each field.
    # Input:  nothing
    # Output: a dictionary, e.g. {"heart_rate": {"average": 80, ...}, ...}
    #         (empty if there are no usable windows)
    def get_summaries(self):
        usable = self.get_usable_observations()
        summaries = {}
        if len(usable) == 0:
            return summaries

        for field_name in MEASUREMENT_FIELDS:
            values = []
            for observation in usable:
                values.append(observation.get_value(field_name))
            summaries[field_name] = calculate_summary(values)
        return summaries

    # Method: compare_with_reference
    # What it does: compares the session averages with the participant's
    #               resting values.
    # Input:  nothing
    # Output: a dictionary with the differences (empty if no usable windows)
    def compare_with_reference(self):
        summaries = self.get_summaries()
        if len(summaries) == 0:
            return {}

        heart_rate = summaries["heart_rate"]["average"]
        resting_hr = self.participant.resting_heart_rate
        return {
            "heart_rate_difference": round(heart_rate - resting_hr, 1),
            "heart_rate_percent": percent_difference(heart_rate, resting_hr),
            "skin_response_difference": round(summaries["skin_response"]["average"]
                                              - self.participant.resting_skin_response, 2),
            "temperature_difference": round(summaries["temperature"]["average"]
                                            - self.participant.resting_temperature, 2),
        }


# Class: SessionRules
# What it does: decides the intensity of a session: insufficient data,
#               resting, moderate activity or high activity.
# Input:  nothing when created
# Output: a SessionRules object whose classify() method gives the label
class SessionRules:

    # Method: classify
    # What it does: applies the rules to the usable windows of a session.
    # Input:  session (a TrainingSession object)
    # Output: a tuple (label, explanation), both texts
    def classify(self, session):
        usable = session.get_usable_observations()
        total = len(session.observations)

        if not self.has_enough_data(len(usable), total):
            return ("insufficient data",
                    "Only " + str(len(usable)) + " of " + str(total) + " windows could "
                    "be used. At least " + str(MINIMUM_USABLE_WINDOWS) + " usable windows "
                    "and at least " + str(MINIMUM_USABLE_PERCENT) + " % are needed.")

        average_hr = average_of_field(usable, "heart_rate")
        average_activity = average_of_field(usable, "activity_level")
        hr_percent = percent_difference(average_hr, session.participant.resting_heart_rate)

        facts = ("Average heart rate is " + str(round(average_hr)) + " bpm, which is "
                 + "{:+}".format(hr_percent) + " % compared with the resting value of "
                 + str(session.participant.resting_heart_rate) + " bpm. Average activity is "
                 + str(round(average_activity, 2)) + ".")

        if hr_percent <= RESTING_MAX_HR_PERCENT and average_activity < RESTING_MAX_ACTIVITY:
            return ("resting", facts + " Both are close to resting level.")

        if hr_percent >= HIGH_MIN_HR_PERCENT or average_activity >= HIGH_MIN_ACTIVITY:
            return ("high activity", facts + " This reaches the high-activity limit ("
                    + str(HIGH_MIN_HR_PERCENT) + " % or activity "
                    + str(HIGH_MIN_ACTIVITY) + ").")

        return ("moderate activity", facts + " This is between the resting and "
                "high-activity limits.")

    # Static method: has_enough_data
    # What it does: checks whether there are enough usable windows to trust
    #               a classification. It is static because it only needs the
    #               two numbers, not the session or the rules object.
    # Input:  usable_count (number), total_count (number)
    # Output: True or False
    @staticmethod
    def has_enough_data(usable_count, total_count):
        if total_count == 0:
            return False
        percent_usable = usable_count / total_count * 100
        return usable_count >= MINIMUM_USABLE_WINDOWS and percent_usable >= MINIMUM_USABLE_PERCENT


# Class: RecoveryRules (inherits from SessionRules)
# What it does: uses the same rules as SessionRules, but first checks for
#               recovery. It OVERRIDES classify(). This is needed because a
#               recovery session has high values at the start and low values
#               at the end, so its averages alone would look like "moderate".
# Input:  nothing when created
# Output: a RecoveryRules object whose classify() method gives the label
class RecoveryRules(SessionRules):

    # Method: classify (overrides SessionRules.classify)
    # What it does: returns "recovering" if heart rate and activity clearly drop
    #               near the end; otherwise it uses the parent class rules.
    # Input:  session (a TrainingSession object)
    # Output: a tuple (label, explanation)
    def classify(self, session):
        usable = session.get_usable_observations()
        total = len(session.observations)

        # Recovery needs enough windows at both the start and the end
        if self.has_enough_data(len(usable), total) and len(usable) >= 2 * WINDOWS_TO_COMPARE:
            first_windows = usable[:WINDOWS_TO_COMPARE]
            last_windows = usable[-WINDOWS_TO_COMPARE:]

            start_hr = average_of_field(first_windows, "heart_rate")
            end_hr = average_of_field(last_windows, "heart_rate")
            start_activity = average_of_field(first_windows, "activity_level")
            end_activity = average_of_field(last_windows, "activity_level")

            start_percent = percent_difference(start_hr, session.participant.resting_heart_rate)
            hr_drop = start_hr - end_hr
            activity_drop = start_activity - end_activity

            if (start_percent >= RECOVERY_MIN_START_PERCENT
                    and hr_drop >= RECOVERY_MIN_HR_DROP
                    and activity_drop >= RECOVERY_MIN_ACTIVITY_DROP):
                return ("recovering",
                        "Heart rate fell from " + str(round(start_hr)) + " to "
                        + str(round(end_hr)) + " bpm and activity fell from "
                        + str(round(start_activity, 2)) + " to " + str(round(end_activity, 2))
                        + " between the first and last " + str(WINDOWS_TO_COMPARE)
                        + " windows.")

        # No recovery found: use the normal rules from the parent class
        return super().classify(session)


# ---------------------------------------------------------------------------
# Main program
# ---------------------------------------------------------------------------

# Function: build_session
# What it does: creates the Participant and TrainingSession objects for one
#               scenario from the raw dictionaries.
# Input:  name (text), profile (dictionary), observations (list of dictionaries)
# Output: a TrainingSession object
def build_session(name, profile, observations):
    participant = Participant.from_profile(profile)
    session = TrainingSession(name, participant)
    for data in observations:
        session.add_observation(data)
    return session


# Function: main
# What it does: analyses every scenario and prints a report for each one.
# Input:  nothing
# Output: nothing (prints to the console)
def main():
    rules = RecoveryRules()
    for name, profile, observations in get_all_scenarios():
        session = build_session(name, profile, observations)
        result = analyse_session(session, rules)
        print(create_report(result))
    print("=" * 60)


if __name__ == "__main__":
    main()
