"""
libscheules

Helper classes and wrappers for IN5_schedule_Gantt.

"""

from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterable, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd
from plotly import offline
from plotly.figure_factory import create_gantt
import plotly.graph_objects as go


@dataclass(frozen=True)
class ExperimentDescriptor:
    proposers: str
    task: str
    duration_days: int
    sample_env: str

    @classmethod
    def from_identifier(cls, identifier: str) -> "ExperimentDescriptor":
        parts = identifier.split("-")
        if len(parts) == 5:
            name, a, b, d, e = parts
            task = f"{a}-{b}"
        elif len(parts) == 6:
            name, a, b, c, d, e = parts
            task = f"{a}-{b}-{c}"
        else:
            raise ValueError(f"Unexpected identifier format: {identifier!r}")

        return cls(
            proposers=name,
            task=task,
            duration_days=int(d.replace("d", "")),
            sample_env=e,
        )


class PlanFile:
    def __init__(self, filepath: str | Path):
        self.filepath = Path(filepath)

    def parse(self, print_info: bool = True) -> Tuple[List[str], List[str], List[float]]:
        experiments: List[str] = []
        dates: List[str] = []
        durations: List[float] = []

        with self.filepath.open() as handle:
            for raw_line in handle:
                line = raw_line.strip()
                if not line:
                    continue
                if line.startswith("N"):
                    experiments.append(
                        "-".join(line.split()[1:]).replace(",", "-").replace("_", "-")
                    )
                elif line[0].isdigit():
                    dates.append(" ".join(line.split()[0:1]))
                elif line.startswith("R"):
                    durations.append(float(line.split()[2]))

        if print_info:
            print(f"Nb items in Exp:  {len(experiments)}")
            print(f"Nb items in Date: {len(dates)}")
            print(f"Nb items in Dur:  {len(durations)}")

        return experiments, dates, durations


class Schedule:
    def __init__(self, dataframe: pd.DataFrame):
        self.df = dataframe.copy()

    @classmethod
    def from_plan(
        cls,
        planfile: str | Path,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        print_info: bool = True,
    ) -> "Schedule":
        exp, dates, durs = PlanFile(planfile).parse(print_info=print_info)
        return cls.from_records(dates, exp, durs, start_date=start_date, end_date=end_date)

    @classmethod
    def from_records(
        cls,
        dates: Sequence[str],
        identifiers: Sequence[str],
        durations: Sequence[float],
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> "Schedule":

        # data = pd.DataFrame({"Start": dates, "id_exp": identifiers, "Duration": durations}) # ,<-- old Claude
        data = pd.DataFrame({"Start": dates, "id_exp": identifiers})  # ,<-- new Claude, we will compute duration from the descriptor. (as in the orginl version)
        data["Start"] = pd.to_datetime(data["Start"], format="%m/%d/%Y")
        data = data.fillna(1)

        start_date_ts = pd.to_datetime(start_date)
        data = data.loc[data["Start"] > start_date_ts]
        if end_date is not None:
            end_date_ts = pd.to_datetime(end_date)
            data = data.loc[data["Start"] < end_date_ts]

        data = data.reset_index(drop=True)

        descriptors = data["id_exp"].map(ExperimentDescriptor.from_identifier)
        data["Proposers"] = [desc.proposers for desc in descriptors]
        data["Task"] = [desc.task for desc in descriptors]
        data["AllDays"] = [desc.duration_days for desc in descriptors]
        data["SampleEnv"] = [desc.sample_env for desc in descriptors]
        data["Finish"] = data["Start"] + pd.to_timedelta(data["AllDays"], unit="d")
        data = data.fillna(1)
        data = data[["Task", "Start", "Finish", "Proposers", "AllDays", "SampleEnv", "id_exp"]]

        return cls(data)

    @property
    def start(self) -> pd.Timestamp:
        return self.df["Start"].min()

    @property
    def end(self) -> pd.Timestamp:
        return self.df["Finish"].max()

    def plot_gantt(
        self,
        title: str = "IN5 schedule",
        offline_mode: bool = True,
        feries: Optional[Iterable[str]] = None,
    ) -> go.Figure:
        fig = self.plot_gantt_alone(title)
        timeline = pd.date_range(self.start, self.end, freq="D")
        time_df = pd.DataFrame(index=timeline)
        time_df["IsWE"] = time_df.index.weekday.isin({5, 6}).astype(int)

        one_day_ms = 24 * 60 * 60 * 1000
        fig.add_trace(
            go.Bar(
                x=time_df.index,
                y=time_df["IsWE"] * (len(self.df) + 2),
                base=-1,
                opacity=0.2,
                offset=0.5,
                width=one_day_ms,
                name="Week-end",
                marker={"color": "gray"},
            )
        )

        if feries is not None:
            feries_dates = {pd.to_datetime(ferie) for ferie in feries}
            time_df["IsFerie"] = [1 if date in feries_dates else 0 for date in time_df.index]
            if time_df["IsFerie"].any():
                fig.add_trace(
                    go.Bar(
                        x=time_df.index,
                        y=time_df["IsFerie"] * (len(self.df) + 2),
                        base=-1,
                        opacity=0.2,
                        offset=0.5,
                        width=one_day_ms,
                        name="Ferie ILL",
                        marker={"color": "tomato"},
                    )
                )

        if offline_mode:
            offline.plot(fig, filename=f"{title}.html")

        return fig

    def plot_gantt_alone(self, title: str = "IN5 schedule") -> go.Figure:
        environments = self.df["SampleEnv"].unique()
        colors = [
            "#" + "".join(random.choice("0123456789ABCDEF") for _ in range(6))
            for _ in environments
        ]

        fig = create_gantt(
            self.df,
            index_col="SampleEnv",
            show_colorbar=True,
            reverse_colors=False,
            colors=colors,
            showgrid_x=True,
            showgrid_y=True,
            title=title,
            bar_width=0.5,
        )

        annotations = []
        for idx, row in self.df.reset_index().iterrows():
            annotations.append(
                {
                    "x": row["Start"],
                    "y": row["index"],
                    "text": row["Proposers"],
                    "showarrow": True,
                    "font": {"color": "black"},
                }
            )

        fig["layout"]["annotations"] = annotations
        return fig


def import_from_plan(planfile, PrintInfo=True):
    return PlanFile(planfile).parse(print_info=PrintInfo)


def convert_to_dataframe(Date, Exp, Dur, startDate='2019-06-01', endDate=None):
    return Schedule.from_records(Date, Exp, Dur, start_date=startDate, end_date=endDate).df


def plot_gantt(df, gantt_name="IN5 schedule", OffLine=True, Feries=None):
    schedule = Schedule(df)
    return schedule.plot_gantt(title=gantt_name, offline_mode=OffLine, feries=Feries)


def plot_gantt_alone(df, Title):
    schedule = Schedule(df)
    return schedule.plot_gantt_alone(title=Title)
