"""Generate synthetic EarthRanger subject-group observations for testing the NSD workflow.

The output has the same columns and dtypes as ecoscope-platform's bundled
``get-subjectgroup-observations.example-return.parquet``, so the mocked
``get_subjectgroup_observations`` task can return it in place of EarthRanger data:

    export WT_TASK_MOCK_IO__ECOSCOPE_PLATFORM_TASKS_IO_GET_SUBJECTGROUP_OBSERVATIONS=$PWD/dev/synthetic/subjectgroup-observations.parquet

Four elephants, each following a classic NSD movement pattern, so the plot has a
known, checkable shape per subject:

    Naserian  resident    OU process around one centre; NSD stays flat and low.
                          Also carries a few (0, 0) fixes, which process_relocations
                          must filter out (otherwise NSD jumps to ~2e7 km²).
    Lemayian  migratory   Moves ~35 km in mid-June and back in early September;
                          NSD steps up to a plateau then returns near zero.
    Kipenget  disperser   Drifts steadily away (~0.25 km/day); NSD rises quadratically.
    Nasieku   nomadic     Correlated random walk; irregular NSD. Has a 5-day collar
                          gap in July (no fixes), which shows up as a straight segment.

Usage (any env with numpy, pandas, geopandas, shapely):

    python dev/synthetic_observations.py [-o OUT.parquet] [--seed N] [--interval-min M]
"""

from __future__ import annotations

import argparse
import random
import uuid
from datetime import timedelta, timezone
from pathlib import Path

import geopandas as gpd
import numpy as np
import pandas as pd
from shapely.geometry import Point

START = pd.Timestamp("2026-04-01T16:00:00Z")
END = pd.Timestamp("2026-10-13T14:00:00Z")
EAT = timezone(timedelta(hours=3))
TENANT_ID = "5ae6c42f-1801-4206-baf9-dbfc11783173"
ER_URL = "https://mep-dev.pamdas.org/api/v1.0/subject/"

SUBJECTS = [
    # name, sex, hex, pattern, centre (lat, lon)
    ("Naserian", "female", "#E4572E", "resident", (-1.48, 35.05)),
    ("Lemayian", "male", "#17BEBB", "migratory", (-1.55, 35.20)),
    ("Kipenget", "male", "#FFC914", "disperser", (-1.40, 35.30)),
    ("Nasieku", "female", "#76B041", "nomadic", (-1.62, 34.95)),
]


def km_to_deg(lat: float, dy_km: np.ndarray, dx_km: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    return dy_km / 110.574, dx_km / (111.320 * np.cos(np.radians(lat)))


def ou_track(rng: np.random.Generator, mu: np.ndarray, theta: float = 0.05, sigma: float = 0.35) -> np.ndarray:
    """Ornstein-Uhlenbeck walk (km) pulled toward a moving centre ``mu`` (n x 2), hourly steps."""
    xy = np.zeros_like(mu)
    xy[0] = mu[0]
    for i in range(1, len(mu)):
        xy[i] = xy[i - 1] + theta * (mu[i] - xy[i - 1]) + sigma * rng.standard_normal(2)
    return xy


def ramp(t_days: np.ndarray, t0: float, t1: float) -> np.ndarray:
    return np.clip((t_days - t0) / (t1 - t0), 0, 1)


def make_track(rng: np.random.Generator, pattern: str, t_days: np.ndarray) -> np.ndarray:
    n = len(t_days)
    if pattern == "resident":
        return ou_track(rng, np.zeros((n, 2)))
    if pattern == "migratory":
        out_ = ramp(t_days, 70, 80)  # ~10-20 Jun
        back = ramp(t_days, 153, 162)  # ~1-10 Sep
        frac = (out_ - back)[:, None]
        return ou_track(rng, frac * np.array([25.0, 25.0]))  # ~35 km NE
    if pattern == "disperser":
        return ou_track(rng, t_days[:, None] * np.array([0.15, 0.20]))  # 0.25 km/day
    if pattern == "nomadic":
        heading = np.cumsum(rng.normal(0, 0.8, n)) + rng.uniform(0, 2 * np.pi)
        step = rng.gamma(2.0, 0.12, n)  # km per hour, mean ~0.24
        step[0] = 0
        return np.cumsum(np.c_[step * np.sin(heading), step * np.cos(heading)], axis=0)
    raise ValueError(pattern)


def build(seed: int, interval_min: int) -> gpd.GeoDataFrame:
    rng = np.random.default_rng(seed)
    ids = random.Random(seed)

    def uid() -> str:
        return str(uuid.UUID(int=ids.getrandbits(128), version=4))

    times = pd.date_range(START, END, freq=f"{interval_min}min")
    frames = []
    for name, sex, hex_, pattern, (lat0, lon0) in SUBJECTS:
        t = times + pd.to_timedelta(rng.integers(-120, 120, len(times)), unit="s")
        t_days = np.asarray((t - START).total_seconds() / 86400.0)
        xy = make_track(rng, pattern, t_days)
        xy += rng.normal(0, 0.03, xy.shape)  # ~30 m GPS error
        dlat, dlon = km_to_deg(lat0, xy[:, 1], xy[:, 0])
        lat, lon = lat0 + dlat, lon0 + dlon

        keep = np.ones(len(t), dtype=bool)
        if pattern == "nomadic":  # 5-day collar gap
            keep &= ~((t >= pd.Timestamp("2026-07-08T00:00Z")) & (t < pd.Timestamp("2026-07-13T00:00Z")))
        t, lat, lon = t[keep], lat[keep], lon[keep]
        if pattern == "resident":  # junk fixes at (0, 0)
            for j in rng.choice(len(t), 3, replace=False):
                lat[j], lon[j] = 0.0, 0.0

        subject_id, source_id = uid(), uid()
        created = pd.Timestamp("2025-02-14T09:30:00", tz=EAT)
        n = len(t)
        frames.append(
            pd.DataFrame(
                {
                    "extra__id": [uid() for _ in range(n)],
                    "extra__location": [{"latitude": a, "longitude": o} for a, o in zip(lat, lon)],
                    "extra__recorded_at": t,
                    "extra__created_at": t + pd.Timedelta(minutes=4),
                    "extra__exclusion_flags": 0.0,
                    "extra__das_tenant_id": TENANT_ID,
                    "extra__source": source_id,
                    "extra__subject_id": subject_id,
                    "geometry": [Point(o, a) for a, o in zip(lat, lon)],
                    "extra__subject__content_type": "observations.subject",
                    "extra__subject__id": subject_id,
                    "extra__subject__name": name,
                    "extra__subject__subject_type": "wildlife",
                    "extra__subject__subject_subtype": "elephant",
                    "extra__subject__common_name": None,
                    "extra__subject__created_at": created,
                    "extra__subject__updated_at": created + pd.Timedelta(days=200),
                    "extra__subject__is_active": True,
                    "extra__subject__user": None,
                    "extra__subject__tracks_available": True,
                    "extra__subject__image_url": "/static/elephant-black.svg",
                    "extra__subject__last_position_status": [
                        {"last_voice_call_start_at": None, "radio_state": "online", "radio_state_at": None}
                    ]
                    * n,
                    "extra__subject__last_position_date": t[-1],
                    "extra__subject__last_position": [
                        {
                            "type": "Feature",
                            "geometry": {"type": "Point", "coordinates": [float(lon[-1]), float(lat[-1])]},
                            "properties": {"title": name, "DateTime": t[-1].isoformat()},
                        }
                    ]
                    * n,
                    "extra__subject__device_status_properties": None,
                    "extra__subject__url": ER_URL + subject_id,
                    "extra__subject__hex": hex_,
                    "groupby_col": subject_id,
                    "fixtime": t,
                    "junk_status": False,
                    "extra__subject__sex": sex,
                }
            )
        )

    df = pd.concat(frames, ignore_index=True)
    df.index = pd.Index(df["extra__id"], name="id")
    return gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")


def summarize(gdf: gpd.GeoDataFrame) -> None:
    """Print each subject's NSD (km², from its first valid fix) at a few points in time."""
    utm = gdf[(gdf.geometry.x != 0) | (gdf.geometry.y != 0)].to_crs("EPSG:32736")
    print(f"{len(gdf)} rows, {gdf['extra__subject__name'].nunique()} subjects, "
          f"{gdf['fixtime'].min()} -> {gdf['fixtime'].max()}")
    for name, g in utm.sort_values("fixtime").groupby("extra__subject__name", sort=False):
        d = g.geometry.distance(g.geometry.iloc[0]) / 1000
        nsd = (d**2).to_numpy()
        q = [nsd[int(f * (len(nsd) - 1))] for f in (0.1, 0.3, 0.5, 0.7, 0.9, 1.0)]
        print(f"  {name:9} n={len(g):5}  NSD km² @10/30/50/70/90/100%: " + " ".join(f"{v:7.0f}" for v in q))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("-o", "--out", type=Path,
                    default=Path(__file__).parent / "synthetic" / "subjectgroup-observations.parquet")
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--interval-min", type=int, default=60, help="fix interval in minutes (default 60)")
    args = ap.parse_args()

    gdf = build(args.seed, args.interval_min)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    gdf.to_parquet(args.out)
    summarize(gdf)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
