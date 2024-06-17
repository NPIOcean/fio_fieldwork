TONe FIO fieldwork repo
-------------------------------------------
Environment adapted from Troll transect 2020-2021 CTD processing, check out readme and manual there for detaield info.

To create the conda environment *fio_seismics* on your system (and download the required packages etc): 

 `mamba env create -f fio_fieldwork_env.yml` 

To activate the environment, enter:

`conda activate fio_fieldwork`

Now, assuming you are still in the base folder of the project repository (where this file is located),  start *jupyterlab*:

`jupyter lab`

Adjustments were made in the parsers for this specific dataset, but also for assessing twin line conductivity and tempeartrue sensors.