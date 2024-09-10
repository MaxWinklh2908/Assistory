# Rapid production

Goal: What is the fastest way to produce an amount of items, given the existing items $S$, goal items $G$ amount and the existing production $E$.

Idea: Discritize the time into N timesteps. Every step, add produced items to the current items and invest into new production facilities using the current items availble.

## Constants
- recipes $ \mathbf{R} = \{1, ..., K\}\\ $
- items $ \mathbf{I} = \{1, ..., M\}\\ $
- timesteps $ \mathbf{T} = \{0, 1, ..., N\}\\ $
- start amount $ \mathbf{S} \\ $
- goal amount $ \mathbf{G} \\ $
- existing recipes $ \mathbf{E} \\ $
- Cost matrix of recipes $ A \\ $
- Production Matrix of recipes $ B \\ $

## Variables

- item i in stock at time t
$$x_{i,t} \in \mathbb{R}^+ \space \forall i \in \mathbf{I}, \space \forall t \in \mathbf{T} $$

- Add/Reduce recipe r at the t (no actions in at step N)
$$z_{r,t} \in \mathbb{Z} \space \forall r \in \mathbf{R},  \space \forall t \in \mathbf{T} $$

Note: The N-th step can be used to dismantle recipes (negative invest) to get items back. However, this could lead to a plan that always includes dismantling the whole facility in the end. TODO

# Helper terms
- Investment costs (items) in recipes at time t (negative for dismantle)
$$
v_{i,t} = \sum_{r \in \mathbf{R}} B_{i,r} z_{r, t}  \space \forall i \in \mathbf{I}, \forall t \in \mathbf{T}
$$

- Production rate at time t (after investment has been applied)
$$ 
p_{i,0} = \sum_{r \in \mathbf{R}} A_{i,r} (E_r + z_{r,0}) \space \forall i \in \mathbf{I}\\
\space \\
p_{i,t} = p_{i,t-1} + \sum_{r \in \mathbf{R}} A_{i,r} z_{r,t} \space \forall i \in \mathbf{I}, \forall t \in \mathbf{T} \setminus \{0, N\} $$

Note: Investment cost is defined for time 0 and N for direct investment and final dismantle. Production rate at time N is not needed as time ends there.

## Objective
Minimize the steps needed to achieve the goal items amount:

$$
\space\\
y_t \in \{0,1\} \space \forall t \in \mathbf{T}\\
\space\\
min \sum_{t \in \mathbf{T}} y_t\\
$$

## Constraints
- Produce until stop. No restart
$$ y_{t} > y_{t-1} \space \forall t \in \mathbf{T} \setminus \{0\} $$

- Update items until not stopped (production rate before after investment)
$$
x_{i,0} = S_i - v_{i,0} \space \forall i \in \mathbf{I}\\
\space\\
x_{i,t} = x_{i,t-1} + y_{t} (-v_{i,t} + p_{i,t-1}) \space \forall i \in \mathbf{I}, \space \forall t \in \mathbf{T} \setminus \{0\}
$$

- Goal items reached at end
$$ x_{i,N} \ge G_i \space \forall i \in \mathbf{I} $$

- Can not invest more than available
$$
x_{i,t} - v_{i,t} \ge 0  \space \forall i \in \mathbf{I}, \forall t \in \mathbf{T}
$$

