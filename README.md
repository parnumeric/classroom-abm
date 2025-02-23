# Agent-based modelling of a classroom

<!-- TOC depthFrom:2 depthTo:6 withLinks:1 updateOnSave:1 orderedList:0 -->

- [Overview](#overview)
- [Running the Mesa model](#running-the-mesa-model)
	- [Contributing to the mesa model:](#contributing-to-the-mesa-model)
- [Multilevel analysis](#multilevel-analysis)
	- [Installation](#installation)
	- [Running the multilevel analysis](#running-the-multilevel-analysis)
	- [Running the full pipeline](#running-the-full-pipeline)
	- [Hamilton supercomputer](#hamilton-supercomputer)
- [Heroku build](#heroku-build)

<!-- /TOC -->


## Overview
This repository uses Agent Based Modelling to model how much students learn according to how good the teacher is at classroom control and teaching.

The first iteration of this project was written in [NetLogo](https://ccl.northwestern.edu/netlogo/index.shtml) and was based on work by Peter Tymms. This is now stored in /NetLogo directory.

We are now developing another model using Mesa (see /MesaModel) and gratefully acknowledge Khulood Alharbi's [model](https://github.com/kuloody/ABM) which was used as a starting point for this work.

## Running the Mesa model

Install the dependencies and activate the Conda environment:

```
conda create --name classroom_abm --file conda_locks/conda-<operating-sys>-64.lock
conda activate classroom_abm
```

Execute python code on command line:

```
cd MesaModel
python run.py
```

More options for running the model:

```
Usage: run.py [OPTIONS]

Options:
  -i, --input-file TEXT       Input file path, relative to current working
                              directory

  -o, --output-file TEXT      Output file path, relative to current working
                              directory

  -p, --n-processors INTEGER  Number of processors to be used by the
                              batchrunner (used only if -a is set)

  -c, --class_id INTEGER      ID of class to run model for
  -a, --all_classes           Whether to run over all classes (overrides
                              class_id; not available in webserver mode)

  -w, --webserver             Whether to run an interactive web server
  -t, --test-mode             Whether to run in test mode (only 10 ticks per
                              day)

  -s, --speedup INTEGER       By how much (approximately) to speed up the
                              model run. The selected speedup will be adjusted
                              to ensure there is a whole number of ticks per
                              day, and at least 1 tick per day.

                              ** NB: Speedup is for use in tests and webserver
                              mode only: should not be used for
                              parameterisation runs. **

  --help                      Show this message and exit.
```

Logging can be configured by two environment variables, `CLASSROOM_ABM_LOG_LEVEL` and `CLASSROOM_ABM_LOG_FILE`. By
default, logging is set to level `INFO` and is output to `stderr`.

To change the log level (e.g. to `DEBUG` for more information):

```bash
export CLASSROOM_ABM_LOG_LEVEL=DEBUG
```

To output the logs to a file (useful because the threads spawned by `BatchRunner` won't write to `stderr`):

```bash
export CLASSROOM_ABM_LOG_FILE='mylogfile.log'
```

A note on webserver mode: when using the webserver mode, a slider is visible that allows users to specify the speed of the model in frames per second. This can be set to a maximum value of 20. Mesa does not offer the facility to increase this range. However, to run the model at maximum speed, users can set the value of frames per second to 0. Mesa interprets this as an instruction to run the model as fast as possible.

To run the model with the full pipeline (including multilevel analysis) see [below](###Running-the-full-pipeline).

### Contributing to the mesa model:

To use Black as a Git hook on all commits run `pre-commit install` from the root of the repository.

Add new dependencies to environment.yml. Then execute `conda-lock` from the root of the repository. This will create lock files for osx, linux and windows which we store in the conda_locks/ directory to minimise clutter:

```
conda-lock --filename-template conda_locks/conda-{platform}.lock
```

To add new dependencies from an updated lock file rerun:

```
conda create --name classroom_abm --file conda_locks/conda-<operating-sys>-64.lock
```

If you add or update any dependencies needed by the Mesa model (rather than test or parameterisation dependencies), please also update `requirements.txt` used by [Heroku](#heroku-build).

## Multilevel analysis

The multilevel_analysis folder contains scripts to run a multilevel model over the data, and calculate a mean square error score. It uses [MLwiN](http://www.bristol.ac.uk/cmm/software/mlwin/) via its R script, R2MLWin.

The R directory contains:

 * A `classroommlm` directory containing an R package with 2 methods, `null_model` and `full_model`, which runs the multilevel model over the given data, and produces the coefficients and variances.
 * A `run_mlm` R project (using `renv` for package management) which imports the CSV `classes_input/test_input.csv` and runs the models from `classroommlm`.

The `multilevel_analysis.py` script runs the multilevel model from R, and calculates the mean squared error. The `run_pipeline.py` script runs the agent based model, then calculautes the mean squared error.

### Installation

  1. Set up and activate a conda environment as above.
  2. Install R (e.g. `brew install R`)
  3. Install MLwiN and mlnscript, for which you will need a license:
    1. Sign up for an academic account at https://www.cmm.bristol.ac.uk/clients/reqform/
    2. Download `mlnscript` for MacOS/linux by filling in form at https://www.cmm.bristol.ac.uk/clients/softwaredownload/
    3. Run the installer (.dmg, .rpm, etc). If prompted for a directory, save the files to a folder such as `/opt/mln`.
    4. If the installer extracts the files to a path other than `/opt/mln`, set an environment variable `MLNSCRIPT_PATH` to where the file `mlnscript` has been saved.
  4. Build the build the `classroommlm` R package and copy the output to the `renv` local packages dir:

  ```bash
  cd multilevel_analysis/R
  R CMD build classroommlm
  cp classroommlm*.tar.gz run_mlm/renv/local
  ```

  (You'll need to do this whenever changes are made in the `classroommlm` directory.)

### Running the multilevel analysis
Run the script from the `multilevel_analysis` directory:

```bash
cd multilevel_analysis
python multilevel_analysis.py
```

Options for running the script:

```bash
Usage: multilevel_analysis.py [OPTIONS]

Options:
  -r, --real-data-file TEXT       File path containing real data, relative to
                                  multilevel_analysis directory. Defaults to
                                  ../classes_input/test_input.csv
  -s, --simulated-data-file TEXT  Output file path, relative to current
                                  working directory  [required]
  --help                          Show this message and exit.
```

### Running the full pipeline
You can run the model and calculate the mean squared error using the `run_pipeline.py` script
from the `multilevel_analysis` directory:

```bash
cd multilevel_analysis
python run_pipeline.py -i ../classes_input/test_input_short.csv
```

`run_pipeline.py` accepts input and output file parameters:

```bash
Usage: run_pipeline.py [OPTIONS]

Options:
  -i, --input-file TEXT         File path containing real data, relative to
                                multilevel_analysis directory. Defaults to
                                ../classes_input/test_input.csv

  -o, --output-file TEXT        Output file path, relative to current working
                                directory.

  -p, --n-processors INTEGER  Number of processors to be used by the
                                batchrunner

  --help                        Show this message and exit.
```

### Hamilton supercomputer

Steps for running the multilevel model on Hamilton are described [here](https://github.com/DurhamARC/classroom-abm/blob/master/hamilton/README.md)
This also documents the ReFrame test infrastructure that we use for parameterisation as well as simple job scripts for running the model on Hamilton.

## Heroku build

The `master` branch is automatically deployed to Heroku, which uses `Procfile`, `requirements.txt` and `runtime.txt` to specify dependencies and how to run. (Contact Alison for info on the Heroku build.)
