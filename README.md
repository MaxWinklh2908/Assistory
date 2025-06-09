# Assistory - Assisting Satisfactory

Supported version of **Satisfactory**: **1.0**

## Overview

### What is Assistory?

Idea: Solve common pioneers problems automatically and/or better. Why? Because there are problems that a computer can solve faster and more reliably than a human. So far, three tools are available:
- [Optimal production](./docs/optimal_production.md): Optimally select recipes for a production plan for multiple concrete use cases
- [Problem monitor](./docs/stats_monitor.md): Get statistics and warnings about problems of your factories via save files
- [Rapid production](./docs/rapid_production.md): Propose a plan when to build what to produce a set of items as fast as possible

### Difference to other tools

- This is a Python3 library with command line applications instead of a web application
- Compared to a classical mod, developing and using **Assistory** does only require Python 3.10 and some packages. No installation of modding toolsets is needed. 
- Problem monitor works fully automatic by detecting and parsing save files
- Fill problem settings (like unlocked recipes) from save files
- Production optimization is extensive and flexible. It uses resource, power and recipe constraints. Objectives include but are not limited to optimization of
    - sink points
    - production item rates while enforcing a ratio
    - number of recipes used
    - a plan with buildings and crafting to reach a milestone as fast as possible

For more details, see the documentation of the single tools above.


### Limitations

**Assistory** consumes data from **Satisfactory** by reading save files but can not write them or control the game.

The optimization tools simplify the concepts of **Satisfactory** to solve problems efficiently. In consequence, results only approximate the optimum. The difference might be neglectible. See [Simplifications](./docs/simplifications.md) to check if your use case might conflict with them.

## Installation

Application was developed and tested in Python3.10 under WSL2 Ubuntu but works in both Linux and Windows.

### Install dependencies
Note: The dependencies in `requirements-full.txt` are only required for optimization. To only display game monitor/stats use `requirements-monitor-only.txt`.

```bash
python3 --version # check for Python 3.10
python3 -m pip install -r requirements-full.txt
```

### Update data.json
All the data of ingame entities is stored in the `data/data.json`. It is up to date to version 1.0. With newer version of **Satisfactory** the file might be outdated. See [this guide](./docs/update_data.md) how to update the `data.json`. 

## Run

See
- [Optimal production](./docs/optimal_production.md)
- [Problem monitor](./docs/stats_monitor.md)
- [Rapid production](./docs/rapid_production.md)

## Assistory Library Tutorial

- [Basics](./example/basics.ipynb)
- [Reading and Writing](./example/read_write.ipynb)
- [Optimization](./example/optimization.ipynb)

## Test
From within the project directory execute:

```
python3 -m unittest discover -s assistory -p "*_test.py"
```

## Theory

Find some theoretical considerations [here](./docs/theory.md)

## Feedback

Feel free to open issues for problems and feature proposals :)
