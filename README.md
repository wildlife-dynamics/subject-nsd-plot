# subject-nsd-plot

Plots Net Squared Displacement (NSD) over time for each subject in an EarthRanger subject group,
chosen from a drop-down of the connected site's subject groups.

## What it does

| Step | What it does |
|---|---|
| **Set Workflow Details** | Add information that will help to differentiate this workflow from another. |
| **Set Time Range** | Choose the period of time to analyze. |
| **Connect to EarthRanger** |  |
| **Set Groupers** |  |
| **Subject Group** | Get observations for a subject group from EarthRanger. |
| **Process Relocations** |  |
| **Relocations To Trajectory** |  |
| **Map Columns** | Maps and transforms the columns of a DataFrame based on the provided parameters. The order of the operations is as follows: drop columns, retain/reorder columns, and rename columns. |
| **Persist Trajectories** | Save a DataFrame to disk with optional sanitization for Arrow compatibility. |
| **Persist Relocations** | Save a DataFrame to disk with optional sanitization for Arrow compatibility. |
| **Split Groups** |  |
| **Draw Ecoplot** | Generates an EcoPlot from the provided params |
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

### Subject Group

| Field | Description | Default |
|---|---|---|
| Subject Group Name *(required)* | A drop-down of the subject groups on the data source chosen above. Pick the data source first; the list loads from it. ⚠️ The use of a group with mixed subtypes could lead to unexpected results | — |

---

## Developing

`spec.yaml` is maintained by hand, not by Ecoscope Studio's designer, because it carries an
`rjsf-overrides` block that Studio doesn't write: it turns **Subject Group Name** into a drop-down
filled by `EarthRangerEnumResolver` from the selected EarthRanger connection. Saving the design
from Studio again would replace the spec and drop that block.

The `studio-run` case in `test-cases.yaml` runs the `elephants` subject group on the `MEP-DEV`
data source.

```bash
# recompile spec.yaml (first time: --install; after that: --update, which bumps VERSION.yaml)
./dev/recompile.sh --update

# run the test cases in test-cases.yaml
pixi run --manifest-path pixi.toml -e default bash dev/pytest-cli.sh subject_nsd_plot --all
```

Documentation: [docs/index.html](docs/index.html).
