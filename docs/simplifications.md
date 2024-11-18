# Simplifications

## Linear power consumption wrt. clock speed
Rational: Only linear problems can be solved efficiently. When using clock rates different from 100% the power consumption must be linear.

Implications: Power consumption is overestimated for the non-integer part of the recipe count. 
Example: Using a recipe 6.5 times with powerconsumption C per building at 100% -> 6 factories at 100%, 1 factory at 50%
- In game: $6*C + 0.5^{1.32}*C \approx 6.4*C $
- Linear: $6*C + 0.5*C = 6.5*C $


## No Desc_FrackingSmasher_C
Rational: Resource Well Pressurizer (Desc_FrackingSmasher_C) is only consuming energy while Resource Well Extractor (Desc_FrackingExtractor_C) is only extracting resources. To use the extractor there needs to be a smasher and a varying number of extractors can be connected with a smasher depending on the location on the map. This concept would involve lots of modeling. Instead the power consumption of the Resource Well Pressurizer is distributed over the Resource Well Extractors based on the available resource wells on the map: The average of number satellites per smasher is 6.941 (See [concept resource wells](./concept_resource_wells.md))

Implications: The actual power consumption will slightly differ from the one calculated depending on the utilization and the composition of the resouce well pressurizer.


## Stable power
Rational: Some building have varying power consumption. Once could now model the best, average of worst case. The average case is used.

Implications: The factory build needs to add batteries with a power feed based on the maximal power consumption overload.


## Only production buildings and recipes
Rational: Many buildings are defined in the game. To reduce complexity of the configurations only the production facilities, i.e. the ones procuding or consuming power or items, are included into the modeling as recipes.

Implications: Some items will be ignored.


## Rational number format for item amounts
Rational: Item amounts in Satisfactory are integer values. Only linear problems can be solved efficiently, thus, rational number are required

Implications: The inventory in an optimal state could contain fractions of an item. This number will still respect the stack size limits


## Only one manual task can be done per time step
Rational: Reduce number of parameters for optimization in the rapid production problem

Implicaitons: In reality, manual work could be executed more flexibly. The difference depends on the time step size (large time step size = manual work modeled very inefficiently)

## No Alien Power Augmentor
This feature is not yet supported in the model. The existance of buildings in the game has no influence when loading save files to initialize problem settings.
