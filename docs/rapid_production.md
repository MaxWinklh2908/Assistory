# Rapid production
Warning: The tool is in an early state and not stable.

Goal: What is the fastest way to produce an amount of items, given existing items and an existing production.

## Functionality

Optimized variables (over all time steps t):
- items in stock at time t
- recipes in production layout at time t
- use of handcrafted recipes at time t

Objective: Minimize the number of time steps to build up a production and produce the required items

The optimization is run in binary search over the number of time steps using a fixed step duration. Note that smaller time step size improves the result but a higher number of steps increases the complexity of the problem which slows down the optimization.

For more details see [mathmatical definition](./rapid_production_definition.md) of the problem.

## Run
```
python3 main_rapid_production.py [-h] compressed_save_file target_item_file
```
Use option `-h` for help.

## Output

Input status:
```
Extracted existing production:
Recipe_IngotCopper_C 0.9991363260132656
Recipe_Wire_C 0.9996157436874462
```

Binary search:
```
Test most relaxed conditions first...
Number of variables = 12684
Number of constraints = 8019
Problem processed in 116812 milliseconds
Search value:  10
Problem processed in 24929 milliseconds
Search value:  4
Problem processed in 8486 milliseconds
Search value:  1
Problem processed in 2604 milliseconds
Search value:  2
Problem processed in 5968 milliseconds
Search value:  3
Problem processed in 4507 milliseconds
Minimal number of steps: 3
```

Result:
```
State
0 {}
1 {'Desc_CopperIngot_C': 14.98, 'Desc_OreCopper_C': 30.03, 'Desc_Wire_C': 29.99}
2 {'Desc_CopperIngot_C': 14.96, 'Desc_OreCopper_C': 0.05, 'Desc_Wire_C': 89.98}
3 {'Desc_CopperIngot_C': 29.94, 'Desc_OreCopper_C': 30.08, 'Desc_Wire_C': 119.97}

Recipe Plan (step, recipes, handcrafted)
0 {} {'Recipe_HandcraftOreCopper_C': 1.0}
1 {} {'Recipe_Wire_C': 1.0}
2 {} {'Recipe_HandcraftOreCopper_C': 1.0}
3 {} {}
```

## Known issues
The optimization currently takes very long due to the high amount of variables.

If there are already some production facilities, the equivalent item value should be used as start items. If the buildings remain as existing recipes the flow should only be positive or sufficient items must be in the inventory to bridge to time for the optimizer to rebuild the missing production 