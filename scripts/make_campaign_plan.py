#!/usr/bin/env python3
from pathlib import Path
import yaml

c = yaml.safe_load(Path("config/campaign.yaml").read_text())
reps = int(c["repetitions"])
ids = [x["id"] for x in c["controlled_conditions"]]
ids += [pid for const in c["tle_campaign"]["constellations"] for pid in const["ids"]]
out = Path("results/freeze/campaign_plan.tsv")
out.parent.mkdir(parents=True, exist_ok=True)
with out.open("w") as f:
    f.write("# condition_id\trepetition\n")
    for condition in ids:
        for rep in range(1, reps + 1):
            f.write(f"{condition}\t{rep}\n")
print(out)
