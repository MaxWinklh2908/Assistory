# Assistory - Assisting Satisfactory
**WARNING: This is still an alpha version**

## Overview

### What is Assistory?

Idea: Solve common pioneers problems automatically and/or better. Why? Because there are problems that a computer can solve faster and more reliably than a human. So far, three tools are available:
- [Optimal production](./docs/optimal_production.md): Optimally select recipes for a production plan for multiple concrete use cases
- [Problem monitor](./docs/stats_monitor.md): Get statistics and warnings about problems of your factories when saving the game
- *Unstable: [Rapid production](./docs/rapid_production.md): Propose a plan when to build what to produce a set of items as fast as possible*

### Difference to other tools
- Extensive and flexible production optimization using resource, power and recipe constraints. Objectives include but are not limited to optimization of
    - sink points
    - production item rates while enforcing a ratio
    - number of recipes used
- Python library with command line applications instead of web application
- [Problem monitor](./docs/stats_monitor.md) works fully automatic by detecting and parsing save files
- Save file reader to automatically fill problem settings (*WIP*)
- *Unstable: Calculate a fully optimized plan with buildings and crafting to reach a milestone as fast as possible*.

For more details, see the documentation of the single tools above.


Compared to a classical mod, developing and using **Assistory** does only require Python 3.10 and some packages. No installation of modding toolsets is needed. **Assistory** consumes data from the game by reading save files but can not control the game.

### Simplifications
The optimization tools simplify the concepts of Satisfactory to solve problems efficiently. In consequence, results only approximate the optimum. The difference might be neglectible. See [Simplifications](./docs/simplifications.md) to check if your use case might conflict with them.

## Installation

Application was developed and tested in Python3.10 under WSL2 Ubuntu but works in both Linux and Windows.

### Install dependencies
Note: The dependencies are only required for optimization. To display game monitor/stats no installation is required.

```bash
python3 --version # check for Python 3.10
python3 -m pip install -r requirements.txt
```

### Import data.json
All the data of ingame entities is stored in the `data/data.json`. This file can be created by [this fork](https://github.com/MaxWinklh2908/SatisfactoryTools/tree/release-1.0) of [SatisfactoryTools by greeeny](https://github.com/greeny/SatisfactoryTools). If you want to use the containerized version, use the branch `containerized-data-generation` and follow the Installation steps.

Alternatively, use the file `data.1.0.json` (potentially outdated compared to the current build) from the original repository [here](https://github.com/greeny/SatisfactoryTools/blob/master/data/data1.0.json) and start directly with the last of the folloing steps, by replacing `/path/to/SatisfactoryTools/data/data.json` with the path to the downloaded `data.1.0.json`.

Follow these steps:

1. Clone the fork repo and follow the installation (or use Docker later)

1. Get the Docs.json: The file is located on the computer after installing Satisfactory. See the [wiki page](https://satisfactory.wiki.gg/wiki/Community_resources#Docs.json). Note that there are many versions of the `Docs.json` named differently for each language. Select the file with the desired language e.g. `en-US.json` and copy it to the `/path/to/repo/data/Docs.json`.

1. Change the encoding of the ``Docs.json`` to **utf-8** (see [this issue](https://github.com/greeny/SatisfactoryTools/issues/67))

1. Run the parseDocs command `yarn parseDocs` (or `docker run --rm -v $PWD/data:/app/data -v $PWD/bin:/app/bin statisfactory-tools:latest`)

1. Use the adaptation script `scripts/adapt_data.py` with the path to the generated `data.json` from the previous step: `python3 scripts/adapt_data.py /path/to/SatisfactoryTools/data/data.json`

Now, the tools listed above can be used.

## Theory

Find some theoretical considerations [here](./docs/theory.md)

## Feedback

Feel free to open issues for problems and feature proposals :)