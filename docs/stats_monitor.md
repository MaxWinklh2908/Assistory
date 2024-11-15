# Stats Monitor
This tool helps reaching milestones faster and fixing a broken production. The required information is extracted from a `.sav` file.

## Run
Note: The current production rate is deduced from the production buildings only.

### One-time mode

Read the stats from a save file once.
```
python3 main_game_stats.py [-h] compressed_save_file
```
Use option `-h` for help.

### Watchdog mode

Monitor a directory, e.g. the save file directory, and print the stats for every new file.
```
python3 main_game_monitor.py [-h] directory_to_monitor
```
Use option `-h` for help.

When running in WSL, use the script `windows_to_wsl_game_observer.py` in a **Windows Command Prompt**. It monitors a directory in the Windows file system and copies new files to a directory in the WSL filesystem. The latter directory can then be monitored by the script `main_game_monitor.py`. This is needed, as the filesystem watchdog on windows files is not possible from within WSL.
```
python \\wsl.localhost\Ubuntu_20_04\home\max\satisfactory-optim\scripts\windows_to_wsl_game_observer.py C:\Users\max\AppData\Local\FactoryGame\Saved\SaveGames\76561198973325836 \\wsl.localhost\Ubuntu_20_04\home\max\satisfactory_save_games
```

### Output

Output of the sav file parsing (example):
```
build_version: 366202
[8] Read levels...
sublevel_count: 6
[69792] Read levels
[405663] Read object headers...
[606445] Read objects...
[1741613] WARNING: Unknown set type: StructProperty
```

The stats module prints 

- the status of factory buildings that have a problem (``Factory status (Problem!)``). Format:
```
{building_name} {building_position} [{clock_rate}x {productivity}%]: {recipe_name} {list of problems}
```
- Milestone/Game Phase Projection. Lists items required for the goal. Format:
```
{item_name}: {items_delivered}/{items_required} + {production_rate}/min => {time_to_finish} min
```

Output of the stats module (example):
```
WARNING Skip unknown item: Desc_HardDrive_C
--------------------Factory status (Problem!) --------------------------------
Build_MinerMk1_C_2147451653 (-1667.3, -265.7, -4.7) [1.00x 27.0%]: Desc_OreIron_C ['Productivity: 0.27']
Build_MinerMk1_C_2147436043 (-1480.1, -301.9, -5.2) [1.00x 25.3%]: Desc_OreCopper_C ['Productivity: 0.25']
Build_ConstructorMk1_C_2147370819 (-1670.7, -305.8, -6.4) [1.00x 46.5%]: Recipe_IronPlate_C ['Productivity: 0.46']
--------------------Game Phase Progress --------------------------------
WARNING Production paused: Recipe_IronPlate_C
Desc_SpaceElevatorPart_1_C: 0/50 +0.00/min => inf min
Time to finish: inf min
```
