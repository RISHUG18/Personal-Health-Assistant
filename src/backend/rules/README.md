# Health Intelligence Rules Engine

This folder contains the deterministic, config-driven health rules engine for evaluating user lab results and environmental factors. 

## How Thresholds Are Configured

All medical thresholds and environmental check bounds are centralized in `config.json`. There are **no hardcoded medical values** in the Python code itself. This allows non-developers or medical professionals to tune and update ranges dynamically without modifying Python code.

### 1. `config.json` Structure
The root configuration (`config.json`) defines core assessment categories such as `hematology`, `lipid_profile`, `blood_sugar`, and `environment`.

Within each category, specific tests (e.g., `creatinine`, `hemoglobin`) trace to severity boundaries (e.g., `medium_high`, `high_high`, `critical_high`, or `medium_low`, `high_low`). These objects can also provide values by gender:
```json
"kidney_function": {
  "creatinine": {
    "male": {
      "medium_high": 1.3,
      "high_high": 2.0
    },
    ...
```

### 2. Loading the Config (`definitions.py`)
At the top of `definitions.py`, we deserialize `config.json` via the standard `json` module. It sits in memory at the module level as `RULES_CONFIG`:
```python
CONFIG_PATH = os.path.join(os.path.dirname(__file__), "config.json")
with open(CONFIG_PATH, "r", encoding="utf-8") as f:
    RULES_CONFIG = json.load(f)
```

### 3. Targeting Correct Value Scopes (`definitions.py`)
Each metric’s corresponding rule function unpacks its localized variables from `RULES_CONFIG`. For rules mapped to split genders, it will try pulling the exact subset matching the user's fetched gender before forwarding:
```python
def _rule_creatinine(user_id: str, rows: List[LabRow], gender: str) -> AlertRecord:
    cfg = RULES_CONFIG["kidney_function"]["creatinine"]
    gender_cfg = cfg.get(gender, cfg["female"]) # Safely grabs the matched gender thresholds
    return _run_generic_rule(rows, "high_creatinine", ["creatinine"], gender_cfg, "Creatinine", ["urine"])
```

### 4. Evaluating Standard Thresholds (`definitions.py`)
The actual rule engine heavily depends on a generic `evaluate_thresholds(val, ref_min, ref_max, config)` utility script inside `definitions.py`. 

Because you pass it `config` (e.g., `{"medium_high": 1.3, "high_high": 2.0}` string-value mappings subset from the overall file), it dynamically checks dictionary keys rather than hard constraints:
```python
# From `definitions.py` inside `evaluate_thresholds`...
    if "critical_high" in config and val > config["critical_high"]:
        return Severity.HIGH
    if "medium_high" in config and val > config["medium_high"]:
        return Severity.MEDIUM
```
By making the conditions evaluate `in config` keys explicitly, updating or providing a new classification band entirely lives within `config.json`.

### 5. Evaluating Environmental Thresholds (`engine.py`)
Similar data-driven logic handles AQI, humidity, and temperature modifiers. In `engine.py`, the `_apply_environmental_modifiers` function loads its respective node dicts from `config.json`, matching active levels without any explicit code backups/overrides:
```python
# From `engine.py` inside `_apply_environmental_modifiers`...
    if "plus_two" in env_cfg["aqi"] and aqi > env_cfg["aqi"]["plus_two"]:
        bump = 2
```
This forces severity spikes based exclusively on the bounding attributes available in `config.json`'s `environment` array.
