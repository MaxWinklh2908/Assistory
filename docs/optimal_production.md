# Optimal Production

Calculate the number of each recipe to optimize the production with respect to a given objective. The optimization is constrained by available power, resource nodes and other aspects depending on the objective.

## Optimization concept

Optimized variables:
- Aggregated productivity rate for each recipe (e.g. 5.3x **Recipe_IngotCopper_C**, 0.8x **Recipe_AILimiter_C**, etc.)

Possible objectives:
- Maximize sink points earning rate (use method `set_objective_max_sink_points`)
- Minimize resources that need to be extracted from resource nodes or resource wells (use method `set_objective_min_resources_spent`)
- Minimize overall number of recipes (use method `set_objective_min_recipes`)
- Maximize sell rate of an item (use method `set_objective_max_item_rate`)

Only one objective can be used at a time.

Default constraint parameterization:
- Existing item production which can be consumed (use constructor parameter `items_available`)
- Allow production of non-sellable items. e.g. **Desc_NuclearWaste_C** (use constructor parameter `TODO`)
- Enforce balance of produced and consumed power (use constructor parameter `TODO`)
- Maximal available resource nodes (use constructor parameter `resource_nodes_available`)

Possible additional constraints:
- Production rate ratio (use method `define_sell_rate_ratio`)
- Minimal production rate (use method `define_sell_rates`)

## Use cases

- Make the most sink points per minute from resources (use `set_objective_max_sink_points`).
- Produce the maximal possible rate of an item (use `set_objective_max_item_rate`)
- Maximize the output rate of multiple items while enforcing a ratio between the output rates (use `set_objective_max_item_rate` and `define_sell_rate_ratio`)
- Minimize the amount of resources used to achieve a given production rate of items (use `set_objective_min_resources_spent` and `define_sell_rates`)
- Minimize the number of buildings used to achieve a given production rate of items to reduce the effort to implement a production plan (use `set_objective_min_recipes` and `define_sell_rates`)

## Run
```
usage: main_optimal_production.py [-h] [--out OUT] [--debug] [--store-rounded] optimal_production_config

positional arguments:
  optimal_production_config
                        Path to an OptimalProductionConfig

optional arguments:
  -h, --help            show this help message and exit
  --out OUT             Output path to the production plan, i.e. recipe amounts by recipe name
  --debug               If the optimization fails with status infeasible, run checks on the problem configuration
  --store-rounded       Additionally, store the production plan rounded to ROUND_NDIGITS digits
```

Additionally, the [optimal production notebook](../optimal_production.ipynb) can be used as interactive application.

For details about the configuration file, see the classes
1. `OptimalProductionProblemUserConfig` in [main_optimal_production.py](../main_optimal_production.py)
2. `StaticProductionLPConfig` in [static_production_problem_config.py](../assistory/optim/static_production_problem_config.py)

## Output

The result of the optimization is a recipe file if the problem can be solved. It contains the amount (potentially non-integer) of recipes of each type to bring running to achieve the objective.

### Console
```
Updated available resources:
Desc_Coal_C-non_fracking       67.0
...
special__power-non_fracking    29.5

Power consumption
AssemblerMk1((1.442, 1)) = 21.63 MW
...
OilRefinery((0.084, 1)) = 2.52 MW
Total consumption: 56.455 MW

Required resource nodes:
Desc_Stone_C-non_fracking = 0.0
Desc_OreIron_C-non_fracking = 0.042
...
Desc_Water_C-fracking = 0.0

Objective value = 2.4

Problem solved in 24 milliseconds
```

### Output file
The **.yml** output file is generated when using the `--out` argument. It contains the amount of recipes. To follow the optimization, update the production accordingly.

Example recipes **.yml** file:
```
Recipe_Alternate_BoltedFrame_C: 0.35714283372674677
Recipe_Alternate_CokeSteelIngot_C: 0.06654761961173436
Recipe_Alternate_HeavyOilResidue_C: 0.04184225903868316
Recipe_Alternate_ModularFrameHeavy_C: 0.5333333147896661
Recipe_Alternate_ModularFrame_C: 0.04365088979876209
Recipe_Alternate_Plastic_1_C: 0.00021667281786600748
Recipe_IngotIron_C: 6.953875223795572e-08
Recipe_MinerMk2OreCopper_C: 1.0430812835693361e-07
Recipe_MinerMk2OreIron_C: 0.0415923839501504
Recipe_MinerMk2Stone_C: 7.450580596923828e-09
Recipe_ModularFrame_C: 1.0416666418313982
Recipe_OilPumpLiquidOil_C: 0.010460564759670792
Recipe_PetroleumCoke_C: 0.04159226225733398
Recipe_SteelPipe_C: 0.22182539870578122
Recipe_WaterPumpWater_C: 3.7749608357747394e-07
```

Note: Consider option `--store-rounded` to additionally generate a file with rounded values

## Background
Sink point value concept of items:
- Standard recipes: value(items_out) = 2 * value(items_in)
- Packaging recipes: value(items_out) = value(items_in)
- Solutions: value(items_out) = value(items_in)
- Exceptions: Alumina Solution, others?
- Alternative recipes: Not clear

## Visualize
The output recipes can be exported to a graph file using [main_export_graph.py](../main_export_graph.py). Then, they can be visualized with graph software (e.g. Gephi). For more details see [Graph export](./graph_export.md)
