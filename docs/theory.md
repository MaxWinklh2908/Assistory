# Theory behind the optimization

## Power consumption
In **Satisfactory**, the power consumption can be reduced by spliting a recipe at 100% clock speed into to buildings with 50% clock speed. That is because the power consumption is growing polynomially, see [Satisfactory Wiki](https://satisfactory.wiki.gg/wiki/Clock_speed)) not linear. 

Splitting the recipe can be described as:

$$
k * power(\frac{1}{k}) = k * (\frac{1}{k})^{N} = k * (\frac{1}{k}) * (\frac{1}{k})^{N-1} = (\frac{1}{k})^{N-1}
$$

where

$$
power(rate) = rate^{N} \\
$$


In consequence, splitting a single recipe into infinitely many machines reduces the power consumption to 0. Prove:

$$
lim_{k \to \inf} (\frac{1}{k})^{N-1} = (\frac{1}{\inf})^{N-1} = 0
$$
Note: $N = log_2{2.5} \approx 1.3 \rightarrow N -1 \approx 0.3 > 0 $

## Maximal sink points per minute
Recipes (usually) double the number of sink points of an item by processing it. Example:
- 1 iron ore (Desc_OreIron_C): 1x1 = 1
- -> 1x iron ingot (Desc_IronIngot_C): 1x2 = 2
- -> 1x iron rod (Desc_IronRod_C): 1x4 = 4
- -> 4x screw (Desc_IronScrew_C): 4x2 = 8

The longer the chain of steps an items is processed by, the higher the sink points worth. However, it is not trivial to optimize sink points by only producing the most advanced item because some recipes, e.g. alternative and packaging, do not stick to this scheme. Also, resources can take different paths to reach the same product. Therefore, linear optimization with flow constraints is needed.
