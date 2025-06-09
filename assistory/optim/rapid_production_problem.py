"""
While static_production_problem.py calculates a facotry as a build blueprint, this
script calculates the fastest way create a set of items. The basic network flow is shared in the modeling
"""
from typing import Tuple, Optional

from assistory.optim.static_flow_problem import ReturnCode
from assistory.optim.iterative_production_problem import IterativeProductionProblem
from assistory.optim.rapid_production_problem_config import RapidProductionProblemConfig
from assistory.optim.rapid_plan import RapidPlan


class RapidProductionProblem:
    """
    Problem of the minimal number of steps to produce a goal amount of items.
    """

    def __init__(self, problem_conf: RapidProductionProblemConfig):
        self.objective_value: Optional[float] = None

        self.problem_conf = problem_conf
        self.problem = None

    def optimize(self, verbose: bool=False) -> Tuple[ReturnCode]:
        """
        Find the fastest solution of the rapid production problem with the given
        settings by binary search over the number of iterations

        Args:
            verbose (bool): Print progress of the optimization. Defaults to False.

        Returns:
            Tuple[ReturnCode, int]: The return code of the optimization.
        """
        if self.objective_value != None:
            raise RuntimeError('Problem already optimized')
        if verbose:
            print('Number of involved recipes:', len(self.problem_conf.unlocked_recipes))
            print('Search solution in minimal number of steps')
        # check zero steps
        remaining_G = self.problem_conf.G - self.problem_conf.S
        if all(v <= 0 for v in remaining_G.values()):
            self.objective_value = 0
            return ReturnCode.OPTIMAL

        left = 1
        right = self.problem_conf.maximal_step_count
        mid = right
        minimal_steps = None
        while left <= right:

            if verbose:
                print('-----------------')
                print('Test with #steps: ', mid)
            iterative_problem_conf = self.problem_conf.get_iterative_production_problem_config(mid)
            if verbose:
                print('Create problem...')
            problem = IterativeProductionProblem(iterative_problem_conf)
            if verbose:
                print("Number of variables =", problem.solver.NumVariables())
                print("Number of constraints =", problem.solver.NumConstraints())
                print('Optimize...')
            status = problem.optimize()
            if verbose:
                print(f"Problem processed in {problem.solver.wall_time():d} milliseconds")

            if status == ReturnCode.OPTIMAL:
                if verbose:
                    print('Iterations sufficient')
                # If an optimal solution is found, store the current mid as the best solution
                minimal_steps = mid
                # Try to find a smaller solution, search the lower half
                right = mid - 1
                self.problem = problem
            elif status == ReturnCode.INFEASIBLE_OR_UNBOUNDED:
                if verbose:
                    print('Iterations insufficient')
                # If the problem is infeasible, search the upper half
                left = mid + 1
            else:
                raise RuntimeError(f'Unexpected status: {status}')
            mid = (left + right) // 2

        if left > self.problem_conf.maximal_step_count:
            return ReturnCode.INFEASIBLE_OR_UNBOUNDED

        self.objective_value = minimal_steps
        return ReturnCode.OPTIMAL

    def get_rapid_plan(self) -> RapidPlan:
        """
        Get the optimized rapid plan. Optimization must be finished with
        optimal result before.

        Returns:
            RapidPlan: The plan to reach the optimization target
        """
        if self.objective_value is None:
            raise RuntimeError('Optimization not yet complete or result not optimal')
        if self.objective_value == 0:
            return RapidPlan(0, 1, [], [], [])
        return self.problem.get_rapid_plan()
