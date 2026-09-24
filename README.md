# Smart Fitness Session Analyzer

Selected option for Assignment: Option A – Smart Fitness Session Analyzer
Student name:Roshni Neupane
# Description

This console program analyses simulated measurements from wearable devices used during training sessions. For every session it:

1. creates a participant with personal reference (resting) values;
2. groups the observation windows into a training session;
3. checks each window, rejecting missing or impossible values and flagging windows with low signal quality;
4. calculates the average, minimum and maximum of each measurement;
5. compares heart rate, skin response and temperature with the participant's reference values;
6. classifies the session as *resting*, *moderate activity*, *high activity*, *recovering* or *insufficient data*; and
7. prints a report showing how many windows were usable and why the session received its classification.

Only the Python standard library is used.

## Repository structure

```
your-repository/
|-- README.md           this file
|-- main.py             classes, standalone functions and the main program
|-- sample_data.py      the seven scenarios analysed by the program
|-- data_generator.py   data generator supplied by the instructor (not modified)
|-- tests.py            automated tests (unittest)
|-- requirements.txt    states that no extra packages are needed
`-- .gitignore          stops Python cache files from being committed
```

`data_generator.py` comes from the instructor's starter files. It is placed in the repository root so that the program runs without changing any paths.

## Class design

Every class and function in `main.py` has a comment directly above it describing what it does, its input and its output. A summary is given below.

| Class | What it does | Input | Output |
|---|---|---|---|
| `Participant` | Stores a participant and their resting heart rate, skin response and temperature. | ID, resting heart rate, resting skin response and resting temperature, or a profile dictionary via `from_profile()`. | A `Participant` object. Raises `ValueError` for an empty ID or an impossible reference value. |
| `Observation` | Stores one measurement window and validates it when it is created. | A dictionary with one window of measurements. | An `Observation` object with a list of `errors`, a list of `warnings` and `is_usable()` (True/False). |
| `TrainingSession` | Groups one participant and all their observations, and calculates summaries and comparisons. | A scenario name, a `Participant`, and observation dictionaries added with `add_observation()`. | Usable observations, summaries (average, minimum, maximum) and a comparison with the reference values. |
| `SessionRules` | Classifies a session as insufficient data, resting, moderate activity or high activity. | A `TrainingSession`. | A tuple `(label, explanation)`. |
| `RecoveryRules` | Child class of `SessionRules` that also detects recovery. | A `TrainingSession`. | A tuple `(label, explanation)`: `recovering` if recovery is found, otherwise the parent class result. |

### Standalone functions

| Function | What it does | Input | Output |
|---|---|---|---|
| `check_value(field_name, value)` | Checks one value for being missing, not a number, or out of range. | A field name and a value. | `None` if the value is valid, otherwise a text describing the problem. |
| `calculate_summary(numbers)` | Calculates summary statistics. | A list of numbers. | A dictionary with `average`, `minimum` and `maximum`. |
| `percent_difference(value, reference)` | Calculates how far a value is above or below a reference, in per cent. | Two numbers. | A percentage, e.g. `50.0`. |
| `average_of_field(observations, field_name)` | Calculates the average of one field over several windows. | A list of observations and a field name. | A number. |
| `analyse_session(session, rules)` | Runs the whole analysis for one session. | A `TrainingSession` and a rules object. | The result dictionary (see below). |
| `create_report(result)` | Turns the result into readable text. | The result dictionary. | A text that is printed to the console. |
| `build_session(name, profile, observations)` | Creates the objects for one scenario. | A name, a profile dictionary and a list of observation dictionaries. | A `TrainingSession`. |
| `get_all_scenarios()` (in `sample_data.py`) | Collects all scenarios. | Optional number of windows. | A list of `(name, profile, observations)` tuples. |

### The result dictionary

`analyse_session()` returns a dictionary like this (shortened):

```python
{
    "scenario": "recovery",
    "participant_id": "P004",
    "total_windows": 12,
    "usable_windows": 12,
    "rejected_windows": 0,
    "flagged_windows": 0,
    "problems": [],                      # e.g. ["window 2: heart_rate is missing"]
    "summaries": {"heart_rate": {"average": 96.5, "minimum": 69, "maximum": 121}, ...},
    "comparison": {"heart_rate_difference": 35.5, "heart_rate_percent": 58.2,
                   "skin_response_difference": 0.33, "temperature_difference": 0.27},
    "classification": "recovering",
    "explanation": "Heart rate fell from 116 to 77 bpm and activity fell ...",
}
```

## Object-oriented concepts

- **Composition:** a `TrainingSession` *has a* `Participant` and *has a* list of `Observation` objects. A session consists of these parts; it is not a kind of participant, so composition is the appropriate relationship rather than inheritance.
- **Encapsulation:** the resting heart rate in `Participant` is stored in the protected attribute `_resting_heart_rate` and can only be read and changed through the `resting_heart_rate` property. The setter checks every new value, so an impossible resting heart rate (for example 300 or −5) can never be stored. This value is protected specifically because every classification depends on it.
- **Inheritance and overriding:** `RecoveryRules` inherits from `SessionRules` and overrides `classify()`. A recovery session starts with high values and ends with low values, so its averages resemble moderate activity. The child class therefore checks the trend first, and if no recovery is found it calls `super().classify()` to reuse the parent's rules instead of repeating them. `tests.py` shows that the two classes give different results for the same recovery session.
- **Class method:** `Participant.from_profile()` creates a participant from the generator's profile dictionary. It is needed because the generator uses different key names (such as `baseline_heart_rate`) from the class.
- **Static method:** `SessionRules.has_enough_data()` checks whether enough windows are usable. It is static because it needs only two numbers, not a session or a rules object, and it is used by both the parent and the child class.

## Assumptions and rules

### Validation

A window is **rejected** if the timestamp is not a whole number of 0 or more, or if any value is missing, is not a number, or lies outside these ranges:

| Field | Allowed range |
|---|---|
| `heart_rate` | 30–220 bpm |
| `skin_response` | 0–20 |
| `temperature` | 25–42 °C (skin temperature, which is lower than core body temperature) |
| `activity_level` | 0–1 |
| `signal_quality` | 0–1 |

A window with valid values is **flagged** if its signal quality is below 0.7. Rejected and flagged windows are not used in the calculations, but they are counted and listed in the report.

### Classification rules

The rules are applied in this order:

1. **Insufficient data:** fewer than 4 usable windows, or fewer than 50 % of all windows usable.
2. **Recovering:** the average heart rate of the first 3 usable windows is at least 25 % above the resting heart rate, and between the first 3 and last 3 windows heart rate falls by at least 15 bpm and activity falls by at least 0.2. At least 6 usable windows are required.
3. **Resting:** the average heart rate is at most 15 % above the resting heart rate, and the average activity is below 0.30.
4. **High activity:** the average heart rate is at least 65 % above the resting heart rate, or the average activity is at least 0.67.
5. **Moderate activity:** all other cases.

Heart rate is compared as a percentage of each participant's own resting heart rate, because the same heart rate can be high for one person and normal for another. All limits are defined at the top of `main.py`, so they are easy to change.

The automated tests run each generated scenario with 30 different seeds. The
repository's standard test run uses 12 windows per session.

## Installation and running

Python 3.8 or newer is required. No packages need to be installed.

```bash
git clone https://github.com/roshni-neupane/smart-fitness-analyzer.git
cd smart-fitness-analyzer
python3 main.py
```

On Windows, use `python` instead of `python3`:

```bash
python main.py
```

To run the tests:

```bash
python3 -m unittest tests.py      # Windows: python -m unittest tests.py
```

## Scenarios

| Scenario | Type | Source | Result |
|---|---|---|---|
| `resting` | normal | generator | resting |
| `moderate_activity` | normal | generator | moderate activity |
| `high_activity` | normal | generator | high activity |
| `recovery` | normal | generator | recovering |
| `poor_quality` | invalid data | generator | insufficient data |
| `unusual_some_bad_windows` | unusual | hand-written | moderate activity (3 of 10 windows skipped) |
| `unusual_short_session` | unusual / invalid | hand-written | insufficient data |

## Example output

```
============================================================
Scenario:    recovery
Participant: P004
Windows:     12 usable out of 12 (0 rejected, 0 flagged)
Measurements (usable windows only):
  field                avg     min     max
  heart_rate          96.5      69     121
  skin_response       2.25    1.96    2.57
  temperature        33.05   32.83   33.34
  activity_level      0.51    0.14    0.84
Compared with personal reference:
  heart rate:    +35.5 bpm (+58.2 %)
  skin response: +0.33
  temperature:   +0.27 C
Result:      RECOVERING
Why:         Heart rate fell from 116 to 77 bpm and activity fell from 0.82 to 0.24 between the first and last 3 windows.
============================================================
Scenario:    unusual_some_bad_windows
Participant: P006
Windows:     7 usable out of 10 (2 rejected, 1 flagged)
Problems found:
  - window 2: heart_rate is missing
  - window 4: low signal quality (0.35)
  - window 6: activity_level = 1.4 is outside the allowed range 0 to 1
Measurements (usable windows only):
  field                avg     min     max
  heart_rate         94.43      92      97
  skin_response       1.99     1.9     2.1
  temperature        32.61    32.5    32.7
  activity_level      0.51    0.47    0.55
Compared with personal reference:
  heart rate:    +26.4 bpm (+38.9 %)
  skin response: +0.39
  temperature:   +0.31 C
Result:      MODERATE ACTIVITY
Why:         Average heart rate is 94 bpm, which is +38.9 % compared with the resting value of 68 bpm. Average activity is 0.51. This is between the resting and high-activity limits.
```

Running `main.py` prints a report like this for all seven scenarios.

## Known limitations

- The limits were chosen to fit the simulated data. They are not medically validated and would need adjusting for real wearable data.
- Recovery is detected by comparing only the first 3 and last 3 windows. A session with several peaks, or one where recovery starts in the middle, may not be detected.
- Skin response and temperature are compared with the reference values but are not used in the classification.
- The profile has no reference value for activity level, so activity is compared with fixed limits.
- Flagged windows are skipped completely rather than weighted by their signal quality.
- The program only reads data from Python lists and dictionaries, not from files or live devices.
