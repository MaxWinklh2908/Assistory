# Theory behind the optimization

## Power consumption
In **Satisfactory**, the power consumption can be reduced by spliting a recipe at 100% clock speed into to buildings with 50% clock speed. That is because the power consumption is growing polynomially, see [Satisfactory Wiki](https://satisfactory.wiki.gg/wiki/Clock_speed)) not linear. 

$$
N = log_2{2.5} \approx 1.3 \\
power(rate) = rate^{N} \\
$$

In consequence, splitting a single recipe into infinitely many machines reduces the power consumption to 0. Prove:

$$
k * power(\frac{1}{k}) = k * (\frac{1}{k})^{N} = k * (\frac{1}{k}) * (\frac{1}{k})^{N-1} = (\frac{1}{k})^{N-1}
$$

Case 1: $N -1 > 0$
$$
lim_{k \to \inf} (\frac{1}{k})^{N-1} = (\frac{1}{\inf})^{N-1} = 0
$$

Case 2: $N -1 = 0$
$$
lim_{k \to \inf} (\frac{1}{k})^{N-1} = lim_{k \to \inf} 1 = 1
$$

Case 3: $N -1 < 0$
$$
lim_{k \to \inf} (\frac{1}{k})^{N-1} = {\inf}^{-(N-1)} = \inf
$$

Since $N - 1 \approx 0.3 > 0$, case 1 holds.

## Maximal sink points per minute
Recipes (usually) double the number of sink points of an item by processing it. Example:
- 1 iron ore (Desc_OreIron_C): 1x1 = 1
- -> 1x iron ingot (Desc_IronIngot_C): 1x2 = 2
- -> 1x iron rod (Desc_IronRod_C): 1x4 = 4
- -> 4x screw (Desc_IronScrew_C): 4x2 = 8

The longer the chain of steps an items is processed by, the higher the sink points worth. However, it is not trivial to optimize sink points by only producing the most advanced item because some recipes, e.g. alternative and packaging, do not stick to this scheme. Also, resources can take different paths to reach the same product. Therefore, linear optimization with flow constraints is needed.


## Simplifications

### Linear power consumption wrt. clock speed
Rational: Only linear problems can be solved efficiently. When using clock rates different from 100% the power consumption must be linear.

Implications: Power consumption is overestimated for the non-integer part of the recipe count. 
Example: Using a recipe 6.5 times with powerconsumption C per building at 100% -> 6 factories at 100%, 1 factory at 50%
- In game: $6*C + 0.5^{1.32}*C \approx 6.4*C $
- Linear: $6*C + 0.5*C = 6.5*C $


### No Desc_FrackingSmasher_C
Rational: Resource Well Pressurizer (Desc_FrackingSmasher_C) is only consuming energy while Resource Well Extractor (Desc_FrackingExtractor_C) is only extracting resources. To use the extractor there needs to be a smasher and a varying number of extractors can be connected with a smasher depending on the location on the map. This concept would involve lots of modeling. Instead the power consumption of the Resource Well Pressurizer is distributed over the Resource Well Extractors based on the available resource wells on the map (average of number satellites per smasher is 6.941)

Implications: The actual power consumption will slightly differ from the one calculated depending on the utilization and the composition of the resouce well pressurizer.


### Stable power
Rational: Some building have varying power consumption. Once could now model the best, average of worst case. The average case is used.

Implications: The factory build needs to add batteries with a power feed based on the maximal power consumption overload.


### Only production buildings and recipes
Rational: Many buildings are defined in the game. To reduce complexity of the configurations only the production facilities, i.e. the ones procuding or consuming power or items, are included into the modeling as recipes.

Implications: Some items will be ignored.


### Rational number format for item amounts
Rational: Item amounts in Satisfactory are integer values. Only linear problems can be solved efficiently, thus, rational number are required

Implications: The inventory in an optimal state could contain fractions of an item. This number will still respect the stack size limits


### Only one manual task can be done per time step
Rational: Reduce number of parameters for optimization in the rapid production problem

Implicaitons: In reality, manual work could be executed more flexibly. The difference depends on the time step size (large time step size = manual work modeled very inefficiently)
