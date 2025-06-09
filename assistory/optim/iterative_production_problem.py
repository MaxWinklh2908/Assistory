
import itertools
from typing import Iterable, Optional

import numpy as np
from ortools.linear_solver import pywraplp

from assistory import game
from assistory.game import ItemValues, ItemFlags, RecipeValues, RecipeFlags
from assistory.optim.static_flow_problem import ReturnCode, get_solution_value
from assistory.optim.iterative_production_problem_config import IterativeProductionProblemConfig
from assistory.optim.rapid_plan import RapidPlan


def filter_items(item_values: ItemValues, item_names: Iterable[str]) -> ItemValues:
    return ItemValues(
        {
            item_name: amount
            for item_name, amount in item_values.items()
            if item_name in item_names
        },
        omega=item_names
    )

def filter_recipes(recipe_values: RecipeValues, recipe_names: Iterable[str]) -> RecipeValues:
    return RecipeValues(
        {
            recipe_name: amount
            for recipe_name, amount in recipe_values.items()
            if recipe_name in recipe_names
        },
        omega=recipe_names
    )


class IterativeProductionData:

    def __init__(self, item_names: ItemFlags, recipe_names: RecipeFlags):
        """
        Create a data configuration for the rapid production problem. Use a
        reduced set of items and recipes to simplify the optimization problem.

        Args:
            item_names (ItemFlags): Names of involved items
            recipe_names (RecipeFlags): names of involved recipes
        """
        self.recipes_automated = sorted(game.RECIPE_NAMES_AUTOMATED & recipe_names)
        self.recipes_handcraft = sorted(game.RECIPE_NAMES_HANDCRAFTED & recipe_names)
        self.items = sorted(set(game.ITEMS) & item_names)

    def get_recipe_automated_production_matrix(self) -> np.ndarray:
        """
        Get the production matrix of the automated recipes: The ingredients
        and product rates of each recipe represent one item vector column. The
        order is aligned with the attributes RECIPE and ITEMS.

        Returns:
            np.ndarray: matrix A[i,r]: production rate of item i by recipe r
        """
        # production matrix A_i,r: production rate of item i by recipe r
        A = np.zeros((len(self.items), len(self.recipes_automated)), dtype=float)
        for r, recipe_name in enumerate(self.recipes_automated):
            single_recipe = RecipeValues({recipe_name: 1}, omega=self.recipes_automated)
            item_balance = filter_items(single_recipe.get_item_rate_balance(), self.items)
            A[:, r] = item_balance.as_array()
        return A

    def get_recipe_handcrafted_production_matrix(self) -> np.ndarray:
        """
        Get the production matrix of the handcraft recipes: The ingredients
        and product rates of each recipe represent one item vector column. The
        order is aligned with the attributes RECIPES_HANDCRAFT and ITEMS.

        Returns:
            np.ndarray: matrix A[i,r]: production rate of item i by recipe r
        """
        A = np.zeros((len(self.items), len(self.recipes_handcraft)), dtype=float)
        for r, recipe_name in enumerate(self.recipes_handcraft):
            single_recipe = RecipeValues({recipe_name: 1}, omega=self.recipes_handcraft)
            item_balance = filter_items(single_recipe.get_item_rate_balance_handcraft(), self.items)
            A[:, r] = item_balance.as_array()
        return A

    def get_recipe_automated_cost_matrix(self) -> np.ndarray:
        """
        Get the cost matrix of the automated recipes: The investment costs of
        each recipe represent one item vector column. The order is aligned
        with the attributes RECIPE and ITEMS.

        Returns:
            np.ndarray: matrix A[i,r]: costs of item i for one recipe r
        """
        A = np.zeros((len(self.items), len(self.recipes_automated)), dtype=float)
        for r, recipe_name in enumerate(self.recipes_automated):
            single_recipe = RecipeValues({recipe_name: 1}, omega=self.recipes_automated)
            recipe_costs = filter_items(single_recipe.get_buildings().get_costs(), self.items)
            A[:, r] = recipe_costs.as_array()
        return A


class IterativeProductionProblem:
    """
    While static_production_problem.py optimizes a final state of the factory
    that fulfills the goal in the best possible way, this problem optimizes a
    target over multiple steps. While the first is intended to be used over
    unlimited time, the second has a fixed duration of each step. Power
    constraints are ignored.
    """
    def __init__(self, problem_conf: IterativeProductionProblemConfig, debug: bool=False):

        self.objective_value: Optional[float] = None

        self.data_conf = IterativeProductionData(
            problem_conf.get_items_involved(),
            problem_conf.unlocked_recipes
        )
        
        # ignore uninvolved items in goal
        items_to_produce = ItemFlags(
            {
                item_name
                for item_name, amount in (problem_conf.G - problem_conf.S).items()
                if amount > 0
            }
        )
        items_impossible_to_produce = set(items_to_produce) - set(self.data_conf.items)
        if items_impossible_to_produce:
            raise ValueError('There are items in the goal that can not be '
                             f'produced with the unlocked recipes: {items_impossible_to_produce}')
        problem_conf.G = filter_items(problem_conf.G, self.data_conf.items)

        # ignore uninvolved items in start items
        problem_conf.S = filter_items(problem_conf.S, self.data_conf.items)

        # building costs must be included in unlocked items
        involved_recipes = RecipeValues(omega=problem_conf.unlocked_recipes)
        involved_recipes.set_values(1)
        involved_cost_items = involved_recipes.get_buildings().get_costs().as_dict_ignoring(0)
        impossible_cost_items = set(involved_cost_items) - set(self.data_conf.items)
        if impossible_cost_items:
            raise ValueError(f'Building costs contain uninvolved item(s): {impossible_cost_items}')

        self.problem_conf = problem_conf

        self.solver = pywraplp.Solver.CreateSolver("CBC")
        if not self.solver:
            raise RuntimeError("Could not create CBC solver")

        self._define_problem(debug)

    def _define_problem(self, debug: bool=False):
        if self.problem_conf.step_count < 1:
            raise ValueError('Number of steps must be at least 1')
        
        K = len(self.data_conf.recipes_automated) # number of recipes
        R_automated = list(range(K))
        L = len(self.data_conf.recipes_handcraft) # number of handcraft recipes
        R_handcraft = list(range(L))
        M = len(self.data_conf.items) # number of items
        I = list(range(M))

        # production matrix A_i,r: production rate of item i by recipe r
        A = self.data_conf.get_recipe_automated_production_matrix()
        # cost matrix A_i,r: costs of item i for recipe j
        B = self.data_conf.get_recipe_automated_cost_matrix()
        # handcrafting production matrix A^H_i,r: production rate of item i by recipe r
        A_handcraft = self.data_conf.get_recipe_handcrafted_production_matrix()

        if debug:
            for item_name, balance in self.problem_conf.E.items():
                if balance < 0:
                    print(f'WARNING: Negative balance of item {item_name}: {balance}.'
                        ' This might cause optimization failure if it can not'
                        ' build up production fast enough. Put a sufficient amount'
                        ' of the item into the inventory.')
        E = filter_items(self.problem_conf.E, self.data_conf.items).as_array()
        S = self.problem_conf.S.as_array()
        G = self.problem_conf.G.as_array()
        N = self.problem_conf.step_count
        T = set(range(N + 1))
        F = set(range(N))

        dt = self.problem_conf.step_duration
        if self.problem_conf.handcraft_efficiency < 0 or self.problem_conf.handcraft_efficiency > 1:
            raise ValueError('Handcraft efficiency must be in [0,1] but is ' + str(self.problem_conf.handcraft_efficiency))
        alpha_H = self.problem_conf.handcraft_efficiency

        ############################### Variables #############################
        
        # variable: automated recipes potentially suitably clocked down at step f
        self.z_A = np.zeros((K, len(F)), dtype=object)
        for r, f in itertools.product(R_automated, F):
            self.z_A[r,f] = self.solver.NumVar(0, self.solver.infinity(), f'z^A_{r}_{f}')

        # variable: Upper limit of automated recipes at step f
        self.u_A = np.zeros((K, len(F)), dtype=object)
        for r, f in itertools.product(R_automated, F):
            self.u_A[r,f] = self.solver.IntVar(0, self.solver.infinity(), f'u^A_{r}_{f}')

        # variable: handcraft recipes at step f
        self.z_H = np.zeros((L, len(F)), dtype=object)
        for r, f in itertools.product(R_handcraft, F):
            self.z_H[r,f] = self.solver.NumVar(0, 1, f'z^H_{r}_{f}')

        ############################### Helper ################################

        # helper term: Investment costs on rounded up amounts of automated
        # recipes for step f
        self.v = np.zeros((M, len(F)), dtype=object)
        for f in F:
            self.v[:,f] = B @ self.u_A[:,f]
        
        # helper term: production rate of automated recipes at step f
        self.p_A = np.zeros((M, len(F)), dtype=object)
        for f in F:
            self.p_A[:,f] = A @ self.z_A[:,f]

        # helper term: production rate of handcraft recipes at step f
        self.p_H = np.zeros((M, len(F)), dtype=object)
        for f in F:
            self.p_H[:,f] = A_handcraft @ (self.z_H[:,f])

        # helper term: state = item i in stock at time t
        self.x = np.zeros((M, len(T)), dtype=object)
        for t in T:
            if t == 0:
                self.x[:,0] = S
            else:
                production = dt * (E + self.p_A[:,t-1] + self.p_H[:,t-1])
                self.x[:,t] = self.x[:,t-1] + production

        ############################### Objective #############################

        # objective: minimize invested recipes
        self.solver.Minimize(self.u_A.sum() + self.z_H.sum())
        
        ############################# Constraints #############################

        # constraint: Item amounts in stock (=states) including next investment
        # are nonnegative and investment is affordable
        for i in I:
            for f in F:
                self.solver.Add(self.x[i,f] - self.v[i,f] >= 0)
            self.solver.Add(self.x[i,N] >= 0)

        # constraint: target capital
        for i in I:
            self.solver.Add(self.x[i, N] >= G[i])

        # constraint: Handcraft efficiency reduced by item logistics and recipe change
        for f in F:
            self.solver.Add(sum(self.z_H[:,f]) <= alpha_H)

        # constraint: Rounded up amounts of automated recipes is upper limit for
        # clocked recipes
        for r, f in itertools.product(R_automated, F):
            self.solver.Add(self.z_A[r,f] <= self.u_A[r,f])

    def get_items_in_stock(self, state_id: int) -> ItemValues:
        """
        Get the amount of items in stock at the state.

        Args:
            state_id (int): Index of the state

        Returns:
            ItemValues: Item amounts
        """
        if state_id < 0 or state_id > self.problem_conf.step_count:
            raise ValueError('Invlid state id: ' + str(state_id))
        
        return ItemValues({
            self.data_conf.items[i]: get_solution_value(self.x[i,state_id])
            for i in range(len(self.data_conf.items))
        })

    def optimize(self) -> ReturnCode:
        """
        Find the optimal solution for the problem.

        Returns:
            ReturnCode: The return code of the optimization
        """
        if self.objective_value != None:
            raise RuntimeError('Problem already optimized')
        code = ReturnCode(self.solver.Solve())
        if code == ReturnCode.OPTIMAL:
            self.objective_value = self.solver.Objective().Value()
        return code

    def get_rapid_plan(self) -> RapidPlan:
        """
        Get the optimized rapid plan. Optimization must be finished with
        optimal result before.

        Returns:
            RapidPlan: The plan to reach the optimization target
        """
        if self.objective_value is None:
            raise RuntimeError('Optimization not yet complete or result not optimal')
        return RapidPlan(
            self.problem_conf.step_count,
            step_duration=self.problem_conf.step_duration,
            recipes_handcraft=[
                RecipeValues({
                    self.data_conf.recipes_handcraft[r]: 
                        get_solution_value(self.z_H[r, step_id])
                    for r in range(len(self.data_conf.recipes_handcraft))
                })
                for step_id in range(self.problem_conf.step_count)
            ],
            recipes_automated=[
                RecipeValues({
                    self.data_conf.recipes_automated[r]: 
                        get_solution_value(self.z_A[r, step_id])
                    for r in range(len(self.data_conf.recipes_automated))
                })
                for step_id in range(self.problem_conf.step_count)
            ],
            recipe_factories=[
                RecipeValues({
                    self.data_conf.recipes_automated[r]: 
                        get_solution_value(self.u_A[r, step_id])
                    for r in range(len(self.data_conf.recipes_automated))
                })
                for step_id in range(self.problem_conf.step_count)
            ],
        )