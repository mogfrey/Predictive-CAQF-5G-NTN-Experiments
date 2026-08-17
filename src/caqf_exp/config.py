from __future__ import annotations

from pathlib import Path
from typing import Any
import yaml


class ConfigError(ValueError):
    pass


def load_yaml(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    if not path.exists():
        raise ConfigError(f"Configuration file not found: {path}")
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ConfigError(f"Expected YAML mapping in {path}")
    return data


def validate_campaign(campaign: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if campaign.get("repetitions") != 5:
        errors.append("repetitions must remain 5 unless an approved methodology change is recorded")
    controlled = campaign.get("controlled_conditions", [])
    if len(controlled) != 5:
        errors.append("controlled_conditions must contain exactly 5 approved conditions")
    constellations = campaign.get("tle_campaign", {}).get("constellations", [])
    ids = [pid for c in constellations for pid in c.get("ids", [])]
    if len(ids) != 6:
        errors.append("TLE campaign must contain exactly 6 pass conditions")
    if campaign.get("scientific", {}).get("t_req_s") != [15, 30, 60]:
        errors.append("scientific.t_req_s must be [15, 30, 60]")
    validation = campaign.get("validation", {})
    if validation.get("group_key") != "pass_id" or not validation.get("forbid_group_overlap", False):
        errors.append("validation must group by pass_id and forbid group overlap")
    return errors


def assert_campaign_valid(campaign: dict[str, Any]) -> None:
    errors = validate_campaign(campaign)
    if errors:
        raise ConfigError("Campaign validation failed:\n- " + "\n- ".join(errors))
