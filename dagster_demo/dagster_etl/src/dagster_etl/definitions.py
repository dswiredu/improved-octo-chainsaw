from pathlib import Path
from dagster import Definitions, load_from_defs_folder
from dagster_etl.io_managers.noop_io import NoOpIOManager

auto_defs = load_from_defs_folder(project_root=Path(__file__).parent.parent.parent)

defs = Definitions(
    assets=auto_defs.assets,
    jobs=auto_defs.jobs,
    schedules=auto_defs.schedules,
    sensors=auto_defs.sensors,
    resources={
        "noop_io": NoOpIOManager(),
    },
)
