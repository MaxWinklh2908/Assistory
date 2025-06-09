# Stats Monitor
This tool helps reaching milestones faster and identfies problems of factories. The required information is extracted from a `.sav` file.

## Run
Note: The current production rate is deduced from the production buildings only.

### One-time mode

Read the stats from a save file once.
```
usage: main_game_stats.py [-h] [--out OUT] [--print-problems] [--print-actors] [--print-inventory] [--print-unlocking] [--print-progress] [--print-production] [--print-paused] [--print-occupied-resource-nodes] [--print-all] [--store-rounded] compressed_save_file

positional arguments:
  compressed_save_file  Path to a save file to read stats from

optional arguments:
  -h, --help            show this help message and exit
  --out OUT             Path to an output directory to store game stats
  --print-problems      List all detected problems of factories
  --print-actors        List of all actors
  --print-inventory     Summarize items in player inventory and dimensional depot
  --print-unlocking     List unlocked recipes and factory buildings
  --print-progress      Show progress of milestone and game phase and project goal time
  --print-production    Summarize production statistics
  --print-paused        List paused factories
  --print-occupied-resource-nodes
                        Summarize the number of resource nodes used
  --print-all           Print all stats
  --store-rounded       Additionally, store the files with values rounded to ROUND_NDIGITS digits
```

### Watchdog mode

Monitor a directory, e.g. the save file directory, and print the stats for every new file.
```
usage: main_game_monitor.py [-h] [--print-problems] [--print-actors] [--print-unlocking] [--print-progress] [--print-production] [--print-paused] directory_to_monitor

positional arguments:
  directory_to_monitor  Directory path to monitor for changed or new files

optional arguments:
  -h, --help            show this help message and exit
  --print-problems      List all detected problems of factories
  --print-actors        List of all actors
  --print-unlocking     List unlocked recipes and factory buildings
  --print-progress      Show progress of milestone and game phase and project goal time
  --print-production    Summarize production statistics
  --print-paused        List paused factories
```

When running in WSL, use the script `windows_to_wsl_game_observer.py` in a **Windows Command Prompt**:
```
python \\wsl.localhost\Ubuntu_20_04\home\user\satisfactory-optim\scripts\windows_to_wsl_game_observer.py C:\Users\user\AppData\Local\FactoryGame\Saved\SaveGames\76561198973325836 \\wsl.localhost\Ubuntu_20_04\home\user\satisfactory_save_games
```
It monitors a directory in the Windows file system and copies new files to a directory in the WSL filesystem. The latter directory can then be monitored by the script `main_game_monitor.py`. This is needed, because the filesystem watchdog on windows files is not possible from within WSL.

## Output

Note: There might be content in the save file that is not understood by the parser. These sections are skipped and reported to the output. To extend the parser, see [this guide](./how_to_debug_parser.md).

### Files

When the parameter `--out OUT` is specified the stats are written to files in the `OUT` directory:
```
OUT
├── base_item_rate.yml
├── base_items.yml
├── base_recipe_count.yml
├── occupied_resource_nodes.yml
├── unlocked_buildings.yml
├── unlocked_recipes.yml
└── unlocked_schematics.yml
```

### --print-actors
Example:
```
--------------------Actors--------------------------------
<assistory.save_parser.actor.SchematicManager object at 0x7f8c3c5f0370>
...
Build_GeneratorIntegratedBiomass_C_2146691535 (-1616.4, -331.3, -4.9) [1.00x]: None
```

### --print-inventory
Example:
---------------Player Inventory + Dimensional Depot---------------
Desc_Berry_C                 2
...
Desc_Wire_C                  1188

### --print-unlocking

Example:
```
--------------------Unlock Progress-------------------------------
Unlocked schematics:
['CustomizerUnlock_ColourSwatches_C', ..., 'Schematic_Tutorial5_C']

Unlocked buildings:
['Desc_AssemblerMk1_C', ..., 'Desc_WaterPump_C']

Unlocked recipes:
['Recipe_AILimiter_C', ..., 'Recipe_ZipLine_C']
```

### --print-progress
List items required for the goal and project the completion time based on the item production rate.

Format: `{item_name}: {items_delivered}/{items_required} + {production_rate}/min => {time_to_finish} min`

Example:
```
--------------------Game Phase Progress --------------------------------
Active Phase: GP_Project_Assembly_Phase_3_C
Desc_SpaceElevatorPart_2_C: 52/2500 +10.00/min => 244.80 min
...
Desc_SpaceElevatorPart_5_C: 0/100 +0.00/min => inf min
Time to finish: inf min
--------------------Milestone Progress --------------------------------
Active milestone: Schematic_5-1_C
Desc_CopperSheet_C: 0/500 +0.00/min => inf min
...
Desc_SteelPipe_C: 0/500 +8.25/min => 60.61 min
Time to finish: inf min
```

Hint: The mapping of data item name to ingame item name can be lookup in the data.json file created during install or via the wiki page `https://satisfactory.wiki.gg/` and the search function

### --print-production
Print the aggragated production rate of each item and recipe type. Productivity is the production rate considering the actual productivity while clocking is the theoretical productivity based on the clock rate of the factories.

Example:
```
--------------------Recipe Rates (Productivity/Clocking) --------------------------------
Recipe_Alternate_IngotSteel_1_C: 4.5/4.5
...
Recipe_Wire_C: 7.0/7.0
--------------------Item Rates (Productivity/Clocking) --------------------------------
Desc_Cable_C: 10.0/10.0 items/min
...
Desc_Wire_C: 22.0/22.0 items/min
```

### --print-problems
Print the status of factory buildings that have a problem.

Format: `{building_name} {building_position} [{clock_rate}x]: {recipe_name} | {productivity}% {list of problems}`

Example:
```
--------------------Factory status (Problem!) --------------------------------
Build_GeneratorIntegratedBiomass_C_2146691536 (-1618.8, -328.4, -4.9) [1.00x]: None | 0.0% ['Production not started', 'Input stack is empty']
...
```

### --print-paused
Example:
```
-------------------- Factories paused--------------------------------
Build_MinerMk1_C_2147375437 (-1784.9, -797.9, 34.2) [0.15x]: Recipe_MinerMk1OreGold_C
...
Build_ConstructorMk1_C_2147446195 (-825.6, -327.6, 157.2) [0.25x]: Recipe_IngotSAM_C
```

### --print-occupied-resource-nodes
List the aggregated number of resource nodes occupied for each node type. Note that impure nodes have a available capacity of 0.5, normal nodes of 1.0 and pure nodes of 2.0. The extraction building placed on the node counts accordingly.

Example:
```
--------------------Occupied Resource Nodes-----------------------
Desc_Coal_C-non_fracking      6.0
...
Desc_Stone_C-non_fracking     1.0
```

## Visualize
The extracted recipes **base_recipe_count.yml** can be exported to a graph file. Then, they can be visualized with graph software (e.g. Gephi). For more details see [Graph export](./graph_export.md)
