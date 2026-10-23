# subject-nsd-plot

Plots Net Squared Displacement (NSD) over time for each subject in an EarthRanger subject group,
chosen from a drop-down of the connected site's subject groups.

## What it does

| Step | What it does |
|---|---|
| **Set Workflow Details** | Add information that will help to differentiate this workflow from another. |
| **Set Time Range** | Choose the period of time to analyze. |
| **Connect to EarthRanger** |  |
| **Group Data** | Splits the dashboard into one view per subject and/or time period, or one view of all the data. |
| **Subject Group** | Get observations for a subject group from EarthRanger. |
| **Process Relocations** |  |
| **Relocations To Trajectory** | Joins the fixes into track segments, dropping segments outside the Trajectory Segment Filter limits. |
| **Map Columns** | Maps and transforms the columns of a DataFrame based on the provided parameters. The order of the operations is as follows: drop columns, retain/reorder columns, and rename columns. |
| **Persist Trajectories** | Save a DataFrame to disk with optional sanitization for Arrow compatibility. |
| **Persist Relocations** | Save a DataFrame to disk with optional sanitization for Arrow compatibility. |
| **Split Groups** |  |
| **Draw Ecoplot** | Plots each subject's NSD over time as a `#2E6F95` line, 1.25 px wide. |
| **Persist Text** | Persist text to a file or cloud storage object. |
| **nsd_plot_widget** | Create a plot widget with a single view. |
| **Merge Widget Views** | Merge widgets with the same `title` and `widget_type`. |
| **Gather Dashboard** |  |

## Requirements

- Access to a **EarthRanger** data source, set up as a connection

---

## 1. Load the Workflow

In the workflow runner, add a new template using this repository's URL. Once added, select
**subject-nsd-plot** from the available templates list to load it.

---

## 2. Configure the Workflow

You'll be prompted to fill in the following parameters before running.

### Set Workflow Details

| Field | Description | Default |
|---|---|---|
| Workflow Name *(required)* |  | — |
| Workflow Description |  | `` |

### Set Time Range

| Field | Description | Default |
|---|---|---|
| Since *(required)* | The start time | — |
| Until *(required)* | The end time | — |
| Timezone |  | — |

### Connect to EarthRanger

| Field | Description | Default |
|---|---|---|
| Data source *(required)* | Select one of your configured data sources. | — |

### Group Data

Split the dashboard into one view per subject and/or per time period. Add entries to the **Group by** list; the dashboard filter then switches between the views. Remove every entry to show all the data in a single view.

| Group by entry | What it does | Default |
|---|---|---|
| Category | Group by subject. **Subject Name** is the only category. | One **Subject Name** entry |
| Time | Group by a time period: year, month, year and month, day of the year, day of the month, day of the week, hour or date. | — |

With the default, each subject gets its own NSD plot. Combine Subject Name with a Time entry (e.g. *Year and Month*) for one plot per subject per period.

### Subject Group

| Field | Description | Default |
|---|---|---|
| Subject Group Name *(required)* | A drop-down of the subject groups on the data source chosen above. Pick the data source first; the list loads from it. ⚠️ The use of a group with mixed subtypes could lead to unexpected results | — |

### Relocations To Trajectory

Advanced. Segments outside these limits are removed before NSD is calculated. The defaults (up to 100 km, 48 hours and 500 km/h per segment) keep almost every segment; tighter limits drop more and can change the NSD curve.

| Field | Default |
|---|---|
| Minimum Segment Length (Meters) | `0.001` |
| Maximum Segment Length (Meters) | `100000` |
| Minimum Segment Duration (Seconds) | `1` |
| Maximum Segment Duration (Seconds) | `172800` |
| Minimum Segment Speed (Kilometers per Hour) | `0.01` |
| Maximum Segment Speed (Kilometers per Hour) | `500` |

---

## Developing

`spec.yaml` is maintained by hand, not by Ecoscope Studio's designer, because it carries an
`rjsf-overrides` block that Studio doesn't write: it turns **Subject Group Name** into a drop-down
filled by `EarthRangerEnumResolver` from the selected EarthRanger connection. Saving the design
from Studio again would replace the spec and drop that block.

`rjsf-overrides` also shapes **Group Data**: it titles the list *Group by*, limits the Category entry to
*Subject Name* (`extra__name`), offers Time groupers (`#/$defs/TemporalGrouper`), leaves out Spatial, and
defaults the list to one Subject Name entry.

The trajectory segment filter is left out of `partial` on **Relocations To Trajectory**, so it's on the
form; its defaults are the platform's `TrajectorySegmentFilter` defaults. The dashboard plot widget is
10 × 15 in `layout.json`.

The `studio-run` case in `test-cases.yaml` runs the `elephants` subject group on the `MEP-DEV`
data source.

```bash
# recompile spec.yaml (first time: --install; after that: --update, which bumps VERSION.yaml)
./dev/recompile.sh --update

# run the test cases in test-cases.yaml
pixi run --manifest-path pixi.toml -e default bash dev/pytest-cli.sh subject_nsd_plot --all
```

Documentation: [docs/index.html](docs/index.html).
