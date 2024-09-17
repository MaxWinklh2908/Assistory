# Satisfactory Optimization

## Installation

```
python3 -m pip install -r requirements
```

## Overview

- Sink points: Optimal production
- Rapid production: Propose a plan when to build what to produce a set of items as fast as possible
- Stats monitor: Get statistics and hints to improve the factory

## State Extraction
The current production rate is deduced from the production buildings which are extracted from `.sav` files.

In WSL:
```
python3 game_file_scanner.py /home/max/satisfactory_save_games
```

### With WSL
Filesystem watchdog on windows files is not possible from within WSL. Therefore, use this workaround:

In windows:
```
python \\wsl.localhost\Ubuntu_18_04\home\max\satisfactory-optim\scripts\windows_to_wsl_game_observer.py C:\Users\max\AppData\Local\FactoryGame\Saved\SaveGames\76561198973325836 \\wsl.localhost\Ubuntu_18_04\home\max\satisfactory_save_games
```

## Related Software
- Satisfactory Calculator: ([link](https://satisfactory-calculator.com/))
- SatisfactoryTools: source until update 8 only ([link](https://www.satisfactorytools.com/1.0/), [source](https://github.com/greeny/SatisfactoryTools/tree/dev))
