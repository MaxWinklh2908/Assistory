from typing import Dict, Iterable, List, Tuple, Union


PROBLEMATIC_PRODUCTIVITY = 0.9


class Actor:

     def __init__(self, *, instance_name: str, type_path: str) -> None:
        """
        Create an Actor object

        Args:
            instance_name (str): Unique name of this object
            type_path (str): Type of this object
        """
        self.instance_name = instance_name
        self.type_path = type_path


class Buildable(Actor):
    
    def __init__(self, *, transform: tuple,
                 build_with_recipe: str,
                 swatch_slot: Union[str, None]=None,
                 **kwargs) -> None:
        """
        Create a Buildable object

        Args:
            transform (tuple): position (x,y,z) and orientation (x,y,z,w)
            build_with_recipe (str): Recipe name with which this object was created
            swatch_slot (Union[str, None], optional): Building customization. Defaults to None.
        """
        super().__init__(**kwargs)
        self.transform = transform # xyzw, xyz
        self.build_with_recipe = build_with_recipe
        self.swatch_slot = swatch_slot

    def get_map_position(self) -> Tuple[float]:
        return (
            self.transform[0] / 100.0,
            self.transform[1] / 100.0,
            self.transform[2] / 100.0
        )
    
    def __str__(self) -> str:
        building_name = self.instance_name.split('.')[-1]
        x,y,z = self.get_map_position()
        return f'{building_name} ({x:.1f}, {y:.1f}, {z:.1f})'


class Factory(Buildable):
    
    def __init__(self, *,
                 power_consumption: float=0,
                 pending_potential: float=1.0,
                 is_producing: bool=False,
                 is_production_paused: bool=False,
                 is_productivity_monitor_enabled: bool=False,
                 current_productivity_measurement_duration: float=float('Inf'),
                 current_productivity_measurement_produce_duration: float=0,
                 current_manufacturing_progress: float=0.0, **kwargs) -> None:
        """
        Create an factory that manipulates items and power. # TODO: Split?

        Args:
            power_consumption (float, optional): Amount of consumed power. Produces power if negative. Defaults to 0.
            pending_potential (float, optional): Clock rate of the building. Defaults to 1.0.
            is_producing (bool, optional): Whether the production is active. Defaults to False.
            is_production_paused (bool, optional): Whether the production is manually stopped. Defaults to False.
            is_productivity_monitor_enabled (bool, optional): Whether the productivity is measured. Defaults to False.
            current_productivity_measurement_duration (float, optional): Period of production measurement. Only used if is_productivity_monitor_enabled is true. Defaults to Infinity.
            current_productivity_measurement_produce_duration (float, optional): Period of active production. Only used if is_productivity_monitor_enabled is true. Defaults to 0.
            current_manufacturing_progress (float, optional): Ratio of progress between 0 and 1. Defaults to 0.0.
        """
        super().__init__(**kwargs)
        self.is_producing = is_producing
        self.is_production_paused = is_production_paused
        self.is_productivity_monitor_enabled = is_productivity_monitor_enabled
        self.current_productivity_measurementduration = current_productivity_measurement_duration
        self.current_productivity_measurement_produce_duration = current_productivity_measurement_produce_duration
        self.pending_potential = pending_potential
        self.power_consumption = power_consumption
        self.current_manufacturing_porgress = current_manufacturing_progress

        # might be used by inventory mixins
        self._input_inventory_stacks = []
        self._output_inventory_stacks = []

    def get_productivity(self) -> float:
        """
        If the productivity is monitored get the ratio of the actual
        productivity over the target productivity.

        Returns:
            float: The actual productivity ratio between 0 and 1
        """
        # TODO: When Current, when Last?
        if not self.is_productivity_monitor_enabled:
            return -1
        return (self.current_productivity_measurement_produce_duration
                / self.current_productivity_measurementduration)
    
    def get_effective_rate(self) -> float:
        """
        Calculate the actual production rate. It is based on
        productivity and overclocking.

        Returns:
            float: The actual production rate mulitplier
        """
        return max(0, self.get_productivity()) * self.pending_potential

    def get_problems(self) -> List[str]:
        # TODO: check power connection
        problems = []
        productivity = self.get_productivity()
        if productivity >= 0 and productivity < PROBLEMATIC_PRODUCTIVITY:
            problems.append(f'Productivity: {productivity:.2f}')
        return problems
    
    def __str__(self) -> str:
        productivity = self.get_productivity() * 100
        return super().__str__() + f' [{self.pending_potential:.2f}x {productivity:.1f}%]'


class ItemStack:

    def __init__(self, item_name: str, amount: int, capacity: int) -> None:
        """
        A stack of one item type or and empty stack.

        Args:
            item_name (str): Item name as defined by game.ITEMS or empty string if amount is 0.
            amount (int): Amount of items on stack or 0 if empty.
            capacity (int): Maximal amount of items on stack for this item type
        """
        if len(item_name) == 0 and amount != 0:
            raise ValueError('0 amount only possible with empty string')
        if amount > capacity:
            raise ValueError
        self.item_name = item_name
        self.amount = amount
        self.capacity = capacity

    def is_empty(self) -> bool:
        return self.amount == 0
    
    def is_full(self) -> bool:
        return self.capacity > 0 and self.amount == self.capacity


class InputInventoryMixin:
    
    def __init__(self, inventory_stacks: Iterable[ItemStack]) -> None:
        self.input_inventory_stacks = list(inventory_stacks)

    def get_input_inventory_items(self) -> dict:
        item_amounts = dict()
        for stack in self.input_inventory_stacks:
            if stack.is_empty():
                continue
            item_amounts[stack.item_name] = item_amounts.get(stack.item_name, 0) + stack.amount
        return item_amounts
        

class OutputInventoryMixin:

    def __init__(self, inventory_stacks: Iterable[ItemStack]) -> None:
        self.output_inventory_stacks = list(inventory_stacks)

    def get_output_inventory_items(self) -> dict:
        item_amounts = dict()
        for stack in self.output_inventory_stacks:
            if stack.is_empty():
                continue
            item_amounts[stack.item_name] = item_amounts.get(stack.item_name, 0) + stack.amount
        return item_amounts


class ManufacturingBuilding(Factory, InputInventoryMixin, OutputInventoryMixin):

    def __init__(self, *, input_inventory_stacks: List[ItemStack],
                 output_inventory_stacks: List[ItemStack],
                 current_recipe_name: Union[str, None]=None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.current_recipe_name = current_recipe_name
        self._input_inventory_stacks = input_inventory_stacks
        self._output_inventory_stacks = output_inventory_stacks

    def get_problems(self) -> List[str]:
        probems = super().get_problems()
        if self.current_recipe_name is None:
            probems.append('No recipe selected')
        else:
            for stack in self._input_inventory_stacks:
                if stack.is_empty():
                    probems.append(f'Input stack is empty')
            for stack in self._output_inventory_stacks:
                if stack.is_full():
                    probems.append(f'Output stack of {stack.item_name} is full: {stack.amount}/{stack.amount}')
        return probems
    
    def __str__(self) -> str:
        return super().__str__() + f': {self.current_recipe_name}'


class FrackingBuilding(Factory, OutputInventoryMixin):

    def __init__(self, *, resource_name: str, current_recipe_name: str,
                 output_inventory_stacks: List[ItemStack], **kwargs) -> None:
        """
        Create a Fracking building

        Args:
            resource_name (str): Name of the resource that is extracted
            current_recipe_name (str): Name of the recipe used. This is an
            implementation detail not found in the original game.
            output_inventory_stacks (List[ItemStack]): Stack of items to output
        """
        super().__init__(**kwargs)
        self.resource_name = resource_name
        self.current_recipe_name = current_recipe_name
        self._output_inventory_stacks = output_inventory_stacks

    def get_problems(self) -> List[str]:
        probems = super().get_problems()
        for stack in self._output_inventory_stacks:
            if stack.is_full():
                probems.append(f'Output stack of {stack.item_name} is full: {stack.amount}/{stack.amount}')
        return probems
    
    # TODO: overwrite get_effective_rate based on purity of node
    
    def __str__(self) -> str:
        return super().__str__() + f': {self.resource_name}'


class SchematicManager(Actor):

    def __init__(self, *, purchased_schematics: List[str]=[],
                 active_schematic: Union[str, None]=None,
                 costs_paid_off: Dict[str, Dict[str, int]]=dict(),
                 **kwargs) -> None:
        """
        Create a SchematicManager object

        Args:
            purchased_schematics (List[str]): All purchased schematics. Defaults to [].
            active_schematic (Union[str, None]): If specified this is the current goal. Defaults to None.
            costs_paid_off (Dict[str, Dict[str, int]]): Mapping from schematic name to 
                payoff state as item amount dict. Defaults to dict().
        """
        super().__init__(**kwargs)
        self.purchased_schematics = purchased_schematics
        self.active_schematic = active_schematic
        self.costs_paid_off = costs_paid_off

    def has_active_schematic(self) -> bool:
        return not self.active_schematic is None


class GamePhaseManager(Actor):

    def __init__(self, *, active_phase: Union[str, None],
                 costs_paid_off: Dict[str, int]=dict(),
                 **kwargs) -> None:
        """
        Create a SchematicManager object

        Args:
            active_phase (Union[str, None]):
            costs_paid_off (Dict[str, int]): Item amount. Defaults to dict().
        """
        super().__init__(**kwargs)
        self.active_phase = active_phase
        self.costs_paid_off = costs_paid_off

    def has_active_phase(self) -> bool:
        return not self.active_phase is None


# TODO: GeneratorBuilding (see bio_generator_object.json)
# TODO: Game Phase Progress
# TODO: Character to get Inventory

class World:

    def __init__(self, actors: List[Actor]) -> None:
        self.actors = actors

    def get_factories(self) -> List[Factory]:
        return [actor for actor in self.actors if isinstance(actor, Factory)]
    
    def get_schematic_manager(self) -> SchematicManager:
        selection = [actor for actor in self.actors if isinstance(actor, SchematicManager)]
        if len(selection) != 1:
            raise ValueError('Expect one schematic manager instance')
        return selection[0]
    
    def get_game_phase_manager(self) -> GamePhaseManager:
        selection = [actor for actor in self.actors if isinstance(actor, GamePhaseManager)]
        if len(selection) != 1:
            raise ValueError('Expect one schematic manager instance')
        return selection[0]
