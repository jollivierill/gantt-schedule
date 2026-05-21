"""Utilities to parse user availability files for Gantt schedule tests.

The expected input format is groups of three non-empty lines:
  - a date line starting with a digit (e.g. "06/15/2019")
  - an "R" line where the 3rd token is an epoch timestamp (seconds)
  - an "N" line describing the experiment (starts with "N")

This module provides a single helper `parse_carefully` which returns a
`pandas.DataFrame` with columns: `Experiment, User, Start, Finish, Duration, Bool`.
"""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional
import pandas as pd


def _parse_group(group: List[str], verbose: bool = False) -> Optional[tuple]:
    """Parse a 3-line group and return (experiment_id, start_str, end_ts).

    Returns None if the group is invalid.
    """
    if len(group) != 3:
        if verbose:
            print("Invalid group length:", group)
        return None

    date_line, r_line, n_line = group

    if not date_line or not date_line[0].isdigit():
        if verbose:
            print("Skipping unexpected date line:", date_line)
        return None

    if not r_line.startswith("R"):
        if verbose:
            print("Skipping unexpected R line:", r_line)
        return None

    if not n_line.startswith("N"):
        if verbose:
            print("Skipping unexpected N line:", n_line)
        return None

    try:
        # r_line format is expected to have the epoch timestamp as the 3rd token
        end_ts = int(float(r_line.split()[2]))
    except Exception:
        if verbose:
            print("Failed to parse timestamp from R line:", r_line)
        return None

    experiment_id = "-".join(n_line.split()[1:]).replace(",", "-").replace("_", "-")

    return experiment_id, date_line, end_ts


def parse_carefully(filename: str, print_info: bool = True, verbose: bool = False) -> pd.DataFrame:
    """Parse a user availability file into a pandas DataFrame.

    See module docstring for expected format.
    """
    with open(filename, "r") as fh:
        raw_lines = fh.readlines()

    lines = [ln.strip() for ln in raw_lines if ln.strip()]

    experiments: List[str] = []
    starts: List[datetime] = []
    finishes: List[datetime] = []
    durations_days: List[int] = []

    i = 0
    while i < len(lines):
        # find next date line

        # print(lines[i])

        if not lines[i] or not lines[i][0].isdigit():
            i += 1
            continue

        date_line = lines[i]
        j = i + 1
        if j >= len(lines):
            break

        # Expected R line at j
        if lines[j].startswith("R"):
            # expected N line at k
            k = j + 1
            if k >= len(lines):
                break
            if not lines[k].startswith("N"):
                if verbose:
                    print("Expected N line at index", k, "but got:", lines[k])
                # skip to next potential date after k
                i = k + 1
                continue

            # valid group date_line, R line, N line
            parsed = _parse_group([date_line, lines[j], lines[k]], verbose=verbose)
            if parsed is None:
                i = k + 1
                continue

            exp_id, start_str, end_ts = parsed
            try:
                start_dt = datetime.strptime(start_str.split()[0], "%m/%d/%Y")
            except Exception:
                if verbose:
                    print("Failed to parse start date:", start_str)
                i = k + 1
                continue

            end_dt = datetime.fromtimestamp(int(end_ts))
            dur_days = (end_dt - start_dt).days

            experiments.append(exp_id)
            starts.append(start_dt)
            finishes.append(end_dt.date())
            durations_days.append(dur_days)

            # advance to next after this group
            i = k + 1
            continue

        # If R is missing and next line is N, skip that N (per user's instruction)
        if lines[j].startswith("N"):
            if verbose:
                print("R line missing at index", j, "; skipping N at index", j)
            i = j + 1
            continue

        # otherwise the file is malformed here; skip one and continue searching
        if verbose:
            print("Unexpected line at index", j, ":", lines[j])
        i += 1

    if print_info:
        print(f"Nb items in Exp:  {len(experiments)}")
        print(f"Nb items in Date: {len(starts)}")
        print(f"Nb items in Dur:  {len(durations_days)}")

    df = pd.DataFrame(
        {
            "Experiment": experiments,
            "Start": starts,
            "Finish": finishes,
            "Duration": durations_days,
        }
    )

    df["Bool"] = df.Experiment.map(lambda x: x.split(":")[0].upper() if x else "")
    df["User"] = df.Experiment.map(lambda x: x.split(":")[1] if len(x.split(":")) > 1 else "Unknown")
    df = df[["Experiment", "User", "Start", "Finish", "Duration", "Bool"]]

    return df

