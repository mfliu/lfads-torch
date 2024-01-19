import os
import shutil
from datetime import datetime
from pathlib import Path

from lfads_torch.run_model_decoders import run_model_decoders

# ---------- OPTIONS -----------
PROJECT_STR = "almproj_single_multiregion"
DATASET_STR = "mesoscale_alm_multiregion"
RUN_TAG = datetime.now().strftime("%y%m%d") + "_almproj_single_multiregion"
RUN_DIR = Path("/results/runs") / PROJECT_STR / DATASET_STR / RUN_TAG
OVERWRITE = True
# ------------------------------

# Overwrite the directory if necessary
if RUN_DIR.exists() and OVERWRITE:
    shutil.rmtree(RUN_DIR)
RUN_DIR.mkdir(parents=True)
# Copy this script into the run directory
shutil.copyfile(__file__, RUN_DIR / Path(__file__).name)
# Switch to the `RUN_DIR` and train the model
os.chdir(RUN_DIR)
run_model_decoders(
    overrides={
        "datamodule": DATASET_STR,
        "model": DATASET_STR,
    },
    config_path="../configs/almproj_single_multiregion.yaml",
)
