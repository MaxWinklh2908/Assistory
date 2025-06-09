import math
from typing import Dict, Iterable, List, Tuple, Union, Set

from assistory import game
from assistory.game import ItemValues, RecipeValues, ResourceNodeValues
from assistory.game import SchematicFlags


PROBLEMATIC_PRODUCTIVITY = 0.9
COMPONENT_TYPE = 0
ACTOR_TYPE = 1


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

    @classmethod
    def get_kwargs(cls, obj: dict, components: Dict[str,dict]) -> dict:
        if obj['object_type'] != ACTOR_TYPE:
            raise ValueError('Expect actor')
        kwargs = dict()
        kwargs['instance_name'] = obj['instance_name']
        kwargs['type_path'] = obj['type_path']
        return kwargs
    
    @classmethod
    def create(cls, obj: dict, components: Dict[str,dict]):
        if obj['object_type'] != ACTOR_TYPE:
            raise ValueError('Expect actor')
        return cls(**cls.get_kwargs(obj, components))


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
    
    @classmethod
    def get_kwargs(cls, obj: dict, components: Dict[str,dict]) -> dict:
        kwargs = super().get_kwargs(obj, components)
        transform = (
            obj["pos_x"],
            obj["pos_y"],
            obj["pos_z"],
            obj["rot_x"],
            obj["rot_y"],
            obj["rot_z"],
            obj["rot_w"],
        )
        kwargs['transform'] = transform
        if 'mBuiltWithRecipe' in obj['properties']:
            kwargs['build_with_recipe'] = obj['properties']['mBuiltWithRecipe']['path_name'].split('.')[-1]
        # TODO: swatch_slot=obj['properties']['mCustomizationData']['payload']
        return kwargs

class Factory(Buildable):
    
    def __init__(self, *,
                 current_recipe_name: Union[str,None]=None,
                 power_consumption: float=0,
                 pending_potential: float=1.0, # TODO: understand pending vs. current
                 is_producing: bool=False,
                 is_production_paused: bool=False,
                 is_productivity_monitor_enabled: bool=False,
                 current_productivity_measurement_duration: float=float('Inf'),
                 current_productivity_measurement_produce_duration: float=0,
                 # current_manufacturing_progress: float=0.0,
                 **kwargs) -> None:
        """
        Create an factory that manipulates items and power using a recipe.

        Args:
            current_recipe_name (str): Name of the recipe of this factory.
            power_consumption (float, optional): Amount of consumed power. Produces power if negative. Defaults to 0.
            pending_potential (float, optional): Clock rate of the building. Defaults to 1.0.
            is_producing (bool, optional): Whether the production is active. Defaults to False.
            is_production_paused (bool, optional): Whether the production is manually stopped. Defaults to False.
            is_productivity_monitor_enabled (bool, optional): Whether the productivity is measured. Defaults to False.
            current_productivity_measurement_duration (float, optional): Period of production measurement. Only used if is_productivity_monitor_enabled is true. Defaults to Infinity.
            current_productivity_measurement_produce_duration (float, optional): Period of active production. Only used if is_productivity_monitor_enabled is true. Defaults to 0.
        """
            # current_manufacturing_progress (float, optional): Ratio of progress between 0 and 1. Defaults to 0.0.
        super().__init__(**kwargs)
        self.current_recipe_name = current_recipe_name
        self.is_producing = is_producing
        self.is_production_paused = is_production_paused
        self.is_productivity_monitor_enabled = is_productivity_monitor_enabled
        self.current_productivity_measurementduration = current_productivity_measurement_duration
        self.current_productivity_measurement_produce_duration = current_productivity_measurement_produce_duration
        self.pending_potential = pending_potential
        self.power_consumption = power_consumption
        # self.current_manufacturing_progress # TODO: Not general for all factories. Move to FrackingBuilding and ManufacturingBuilding

    def get_productivity(self) -> float:
        """
        If the productivity is monitored get the ratio of the actual
        productivity over the target productivity.

        Returns:
            float: The actual productivity ratio between 0 and 1. If not
                measured return -1.
        """
        # TODO: When Current, when Last?
        if not self.is_productivity_monitor_enabled:
            raise ValueError('Productivity monitor not enabled')
        if self.current_productivity_measurementduration <= 0:
            return -1
        return (self.current_productivity_measurement_produce_duration
                / self.current_productivity_measurementduration)
    
    def get_potential_rate(self) -> float:
        """
        Get the rate that is defined by the settings of the factory ignoring
        productivity

        Returns:
            float: potential rate
        """
        return self.pending_potential
    
    def get_effective_rate(self) -> float:
        """
        Calculate the actual production rate. It is based on
        productivity and overclocking.

        Returns:
            float: The actual production rate mulitplier
        """
        return max(0, self.get_productivity()) * self.get_potential_rate()

    def get_problems(self) -> List[str]:
        # TODO: check power connection
        problems = []
        if not self.is_production_paused:
            if self.is_productivity_monitor_enabled:
                productivity = self.get_productivity()
                if productivity >= 0 and productivity < PROBLEMATIC_PRODUCTIVITY:
                    problems.append(f'Productivity: {productivity:.2f}')
            else:
                problems.append('Production not started')
        return problems
    
    def __str__(self) -> str:
        return super().__str__() + f' [{self.pending_potential:.2f}x]: {self.current_recipe_name}'

    @classmethod
    def get_kwargs(cls, obj: dict, components: Dict[str,dict]) -> dict:
        kwargs = super().get_kwargs(obj, components)
        prop = obj['properties']
        if 'mProductivityMonitorEnabled' in prop:
            kwargs['is_productivity_monitor_enabled'] = prop['mProductivityMonitorEnabled']['value']
            if kwargs['is_productivity_monitor_enabled']: # True if defined but still check for safety
                cur_prod_measure_duration = prop.get('mCurrentProductivityMeasurementDuration', {'value': 0})['value']
                kwargs['current_productivity_measurement_duration'] = cur_prod_measure_duration
                if 'mCurrentProductivityMeasurementProduceDuration' in prop:
                    kwargs['current_productivity_measurement_produce_duration'] = prop['mCurrentProductivityMeasurementProduceDuration']['value']
                else:
                    # in case the power is shutdown TODO: check otherwise
                    kwargs['current_productivity_measurement_produce_duration'] = 0

        if 'mPendingPotential' in prop:
            kwargs['pending_potential'] = prop['mPendingPotential']['value']
        if 'mIsProducing' in prop:
            kwargs['is_producing'] = prop['mIsProducing']['value']
        if 'mIsProductionPaused' in prop:
            kwargs['is_production_paused'] = prop['mIsProductionPaused']['value']
        # if 'mCurrentManufacturingProgress' in prop:
        #     kwargs['current_manufacturing_progress'] = prop['mCurrentManufacturingProgress']
        # elif 'mCurrentExtractProgress' in prop:
        #     kwargs['current_manufacturing_progress'] = prop['mCurrentExtractProgress']['value']
        # power_info = components[prop['mPowerInfo']['path_name']]
        # if 'mTargetConsumption' in power_info['properties']:
        #     kwargs['power_consumption'] = power_info['properties']['mTargetConsumption']['value']
        # elif 'mDynamicProductionCapacity' in power_info['properties']:
        #     kwargs['power_consumption'] = -power_info['properties']['mDynamicProductionCapacity']['value']

        # current_recipe_name is set by subclasses

        return kwargs


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
            raise ValueError(f'Amount {amount} larger than capacity {capacity}')
        self.item_name = item_name
        self.amount = amount
        self.capacity = capacity

    def is_empty(self) -> bool:
        return self.amount == 0
    
    def is_full(self) -> bool:
        return self.capacity > 0 and self.amount == self.capacity


def create_inventory_stack(item_desc: dict, stack: dict,
                           stacksize_overwrite: float=None) -> ItemStack:
    if stack['prop']['item_name'] != '':
        item_name = stack['prop']['item_name'].split('.')[-1]
        amount = stack['properties']['NumItems']['value']
    elif item_desc['path_name'] != '':
        item_name = item_desc['path_name'].split('.')[-1]
        amount = 0
    else: # must be empty is this case
        return ItemStack('', 0, 0)
    if not item_name in game.ITEMS:
        print('WARNING Skip unknown item:',  item_name)
        return ItemStack('', 0, 0)
    amount = stack['properties']['NumItems']['value']
    if stacksize_overwrite is None:
        capacity = game.ITEMS[item_name]['stackSize']
    else:
        capacity = stacksize_overwrite
    return ItemStack(item_name=item_name, amount=amount, capacity=capacity)


def create_inventory_stacks(component: dict,
                            stacksize_overwrite: float=None
                            ) -> List[ItemStack]:
    if component['object_type'] != COMPONENT_TYPE:
        raise ValueError('Expect component')
    prop = component['properties']

    if 'mAllowedItemDescriptors' in prop and 'elements' in prop['mAllowedItemDescriptors']:
        stack_count =  len(prop['mAllowedItemDescriptors']['elements'])
    elif 'mInventoryStacks' in prop and 'elements' in prop['mInventoryStacks']:
        stack_count =  len(prop['mInventoryStacks']['elements'])
    else:
        return list()

    if not 'mInventoryStacks' in prop or not 'elements' in prop['mInventoryStacks']:
        # required due to a bug in satisfactory-calculator.com
        # TODO: Why does Miner not have mInventoryStacks member?
        stacks = [
            {
                'prop': {'item_name': ''},
                'properties': {'NumItems': {'value': 0}},
            }
            for _ in range(stack_count)
        ]
    else:
        stacks = prop['mInventoryStacks']['elements']

    if not 'mAllowedItemDescriptors' in prop or not 'elements' in prop['mAllowedItemDescriptors']:
        allowed_items = [
            {'path_name': ''}
            for _ in range(stack_count)
        ]
    else:
        allowed_items = prop['mAllowedItemDescriptors']['elements']

    if len(allowed_items) != len(stacks):
        raise ValueError
    # TODO: Why does OutputInventory have extra FGItemDesciptor stack? It means no item allowed
    return [
        create_inventory_stack(allowed_item, stack, stacksize_overwrite)
        for allowed_item, stack in zip(allowed_items, stacks)
        if not 'FGItemDescriptor' in allowed_item['path_name']
    ]


class InputInventoryMixin:
    
    def __init__(self, inventory_stacks: Iterable[ItemStack]) -> None:
        self.input_inventory_stacks = list(inventory_stacks)

    def get_input_inventory_items(self) -> Dict[str, int]:
        """
        Return the items in the inventory. Solid items are given in number,
        liquid items are given in full liters.

        Returns:
            Dict[str, int]: Amount of items by item name
        """
        item_amounts = dict()
        for stack in self.input_inventory_stacks:
            if stack.is_empty():
                continue
            item_amounts[stack.item_name] = item_amounts.get(stack.item_name, 0) + stack.amount
        return item_amounts
        

class OutputInventoryMixin:

    def __init__(self, inventory_stacks: Iterable[ItemStack]) -> None:
        self.output_inventory_stacks = list(inventory_stacks)

    def get_output_inventory_items(self) -> Dict[str, int]:
        """
        Return the items in the inventory. Solid items are given in number,
        liquid items are given in full liters.

        Returns:
            Dict[str, int]: Amount of items by item name
        """
        item_amounts = dict()
        for stack in self.output_inventory_stacks:
            if stack.is_empty():
                continue
            item_amounts[stack.item_name] = item_amounts.get(stack.item_name, 0) + stack.amount
        return item_amounts


class ManufacturingBuilding(Factory, InputInventoryMixin, OutputInventoryMixin):

    def __init__(self, *, input_inventory_stacks: List[ItemStack],
                 output_inventory_stacks: List[ItemStack], **kwargs) -> None:
        super().__init__(**kwargs)
        InputInventoryMixin.__init__(self, input_inventory_stacks)
        OutputInventoryMixin.__init__(self, output_inventory_stacks)

    def get_problems(self) -> List[str]:
        probems = super().get_problems()
        if self.current_recipe_name is None:
            probems.append('No recipe selected')
        elif not self.is_production_paused and probems:
            for stack in self.input_inventory_stacks:
                if stack.is_empty():
                    probems.append(f'Input stack is empty')
                    break
            for stack in self.output_inventory_stacks:
                if stack.is_full():
                    probems.append(f'Output stack of {stack.item_name} is full: {stack.amount}/{stack.amount}')
        return probems

    @classmethod
    def get_kwargs(cls, obj: dict, components: Dict[str,dict]) -> dict:
        kwargs = super().get_kwargs(obj, components)
        prop = obj['properties']
        if 'mCurrentRecipe' in prop:
            kwargs['current_recipe_name'] = prop['mCurrentRecipe']['path_name'].split('.')[-1]
        input_inventory_component = components[prop['mInputInventory']['path_name']]
        kwargs['input_inventory_stacks'] = create_inventory_stacks(input_inventory_component)
        output_inventory_component = components[prop['mOutputInventory']['path_name']]
        kwargs['output_inventory_stacks'] = create_inventory_stacks(output_inventory_component)
        return kwargs


class NodeMixin:

    def __init__(self, resource_node_unique_name: str) -> None:
        """
        There are 4 types of nodes:
        - resource nodes, e.g. iron ore
        - resource wells, e.g. water, liquid oil, nitrogen gas
        - water volumes
        - geyser

        Args:
            resource_node_unique_name (str): The ingame name of the node
        """
        self.resource_node_unique_name = resource_node_unique_name
        self.is_water = 'FGWaterVolume' in resource_node_unique_name

        if resource_node_unique_name in game.UNIQUE_NODES:
            unique_resource_node = game.UNIQUE_NODES[resource_node_unique_name]
            self.resource_name = unique_resource_node['resource']
            self.purity = unique_resource_node['purity']
            self.is_resource_well = unique_resource_node['fracking']
        elif self.is_water:
            self.resource_name = 'Desc_Water_C'
            self.purity = 'normal'
            self.is_resource_well = False
        else:
            raise RuntimeError('Unknown resouce node name: ' + resource_node_unique_name)


class FrackingBuilding(Factory, OutputInventoryMixin, NodeMixin):

    def __init__(self, *, output_inventory_stacks: List[ItemStack],
                 resource_node_unique_name: str, **kwargs) -> None:
        """
        Create a Fracking building

        Args:
            output_inventory_stacks (List[ItemStack]): Stack of items to output
            resource_node_unique_name (str): Unique name of the underlaying resource node
        """
        super().__init__(**kwargs)
        OutputInventoryMixin.__init__(self, output_inventory_stacks)
        NodeMixin.__init__(self, resource_node_unique_name)

    def get_problems(self) -> List[str]:
        problems = super().get_problems()
        if not self.is_production_paused and problems:
            for stack in self.output_inventory_stacks:
                if stack.is_full():
                    problems.append(f'Output stack of {stack.item_name} is full: {stack.amount}/{stack.amount}')
        return problems

    def get_potential_rate(self) -> float:
        """
        Get the production rate based on the clock rate and purity of the node.
        Pure node have double the rate. Impure nodes have half the rate. Ignore
        productivity of the building.

        Returns:
            float: The rate multiplier of the recipe used
        """
        purity_factor = game.PURITY_DURATION_FACTORS[self.purity]
        return super().get_potential_rate() * purity_factor
    
    @classmethod
    def get_kwargs(cls, obj: dict, components: Dict[str,dict]) -> dict:
        kwargs = super().get_kwargs(obj, components)
        prop = obj['properties']
        
        output_inventory_component = components[prop['mOutputInventory']['path_name']]
        stacksize_overwrite = 200_000 if kwargs['build_with_recipe'] == 'Recipe_WaterPump_C' else None
        kwargs['output_inventory_stacks'] = create_inventory_stacks(
            output_inventory_component,
            stacksize_overwrite)
        if not any(len(item_stack.item_name) > 0 for item_stack in kwargs['output_inventory_stacks']):
            raise ValueError('Could not detect resource from output intentory. Data: ' + str(obj['properties']))
        
        kwargs['resource_node_unique_name'] = prop['mExtractableResource']['path_name'].split('PersistentLevel.')[-1]
        
        resource_name =  NodeMixin(kwargs['resource_node_unique_name']).resource_name
        if 'Miner' in kwargs['build_with_recipe']:
            insert_idx = kwargs['build_with_recipe'].find('Miner') + len('MinerMkX')
            kwargs['current_recipe_name'] = (kwargs['build_with_recipe'][:insert_idx]
                        + game.get_bare_name(resource_name)
                        + kwargs['build_with_recipe'][insert_idx:])
        elif kwargs['build_with_recipe'].endswith('Recipe_WaterPump_C'):
            kwargs['current_recipe_name'] = 'Recipe_WaterPumpWater_C'
        elif kwargs['build_with_recipe'].endswith('Recipe_OilPump_C'):
            kwargs['current_recipe_name'] = 'Recipe_OilPumpLiquidOil_C'
        elif kwargs['build_with_recipe'].endswith('Recipe_FrackingExtractor_C'):
            kwargs['current_recipe_name'] = ('Recipe_FrackingExtractor'
                        + game.get_bare_name(resource_name)
                        + '_C')
        else:
            raise NotImplementedError(str(kwargs['build_with_recipe']))
        return kwargs


def generator_recipe_from_building_and_fuel(building_name: str, fuel_name: str) -> str:
    # TODO: Check if there is some other difference
    if building_name == 'Desc_GeneratorIntegratedBiomass_C':
        building_name = 'Desc_GeneratorBiomass_Automated_C'
    recipe_names = {
        recipe_name
        for recipe_name in game.produced_in[building_name]
        if game.RECIPES[recipe_name]['ingredients'][fuel_name] > 0
    }
    if len(recipe_names) != 1:
        raise RuntimeError('Ambigous or no recipe: ' + str(recipe_names))
    return recipe_names.pop()


class GeneratorBuilding(Factory, InputInventoryMixin, OutputInventoryMixin):

    def __init__(self, *, input_inventory_stacks: List[ItemStack],
                 output_inventory_stacks: List[ItemStack], **kwargs) -> None:
        super().__init__(**kwargs)
        InputInventoryMixin.__init__(self, input_inventory_stacks)
        OutputInventoryMixin.__init__(self, output_inventory_stacks)

    def get_problems(self) -> List[str]:
        probems = super().get_problems()
        if not self.is_production_paused and probems:
            for stack in self.input_inventory_stacks:
                if stack.is_empty():
                    probems.append(f'Input stack is empty')
                    break
            for stack in self.output_inventory_stacks:
                if stack.is_full():
                    probems.append(f'Output stack of {stack.item_name} is full: {stack.amount}/{stack.amount}')
                    break
        return probems

    @classmethod
    def get_kwargs(cls, obj: dict, components: Dict[str,dict]) -> dict:
        kwargs = super().get_kwargs(obj, components)
        prop = obj['properties']
        building_name = obj['type_path'].split('.')[-1].replace('Build_', 'Desc_')
        if 'mCurrentFuelClass' in prop:
            fuel_name = prop['mCurrentFuelClass']['path_name'].split('.')[-1]
            kwargs['current_recipe_name'] = generator_recipe_from_building_and_fuel(
                building_name, fuel_name)
        if 'mFuelInventory' in prop:
            input_inventory_component = components[prop['mFuelInventory']['path_name']]
            kwargs['input_inventory_stacks'] = create_inventory_stacks(input_inventory_component)
        else:
            kwargs['input_inventory_stacks'] = []
        if 'mOutputInventory' in prop:
            output_inventory_component = components[prop['mOutputInventory']['path_name']]
            kwargs['output_inventory_stacks'] = create_inventory_stacks(output_inventory_component)
        else:
            kwargs['output_inventory_stacks'] = []
        return kwargs


class AlienPowerBuilding(Factory, InputInventoryMixin):
    
    def __init__(self, *, input_inventory_stacks: List[ItemStack],
                 **kwargs) -> None:
        super().__init__(**kwargs)
        InputInventoryMixin.__init__(self, input_inventory_stacks)

    def get_problems(self) -> List[str]:
        # TODO: comment in and filter problems if power connection check is implemented
        # probems = super().get_problems()
        return []

    @classmethod
    def get_kwargs(cls, obj: dict, components: Dict[str,dict]) -> dict:
        kwargs = super().get_kwargs(obj, components)
        # TODO: Produces base power independent of fuel consumption
        
        prop = obj['properties']

        kwargs['current_recipe_name'] = 'Recipe_AlienPowerBuildingAlienPowerFuel_C'
    
        if 'mFuelInventory' in prop:
            input_inventory_component = components[prop['mFuelInventory']['path_name']]
            kwargs['input_inventory_stacks'] = create_inventory_stacks(input_inventory_component)
        else:
            kwargs['input_inventory_stacks'] = []
        return kwargs


class ThermalGenerator(Factory, NodeMixin):

    def __init__(self, *, resource_node_unique_name: str, **kwargs) -> None:
        """
        Create a Fracking building

        Args:
            resource_node_unique_name (str): Unique name of the underlaying resource node
        """
        super().__init__(**kwargs)
        NodeMixin.__init__(self, resource_node_unique_name)

    def get_potential_rate(self) -> float:
        """
        Get the production rate based on the clock rate and purity of the node.
        Pure node have double the rate. Impure nodes have half the rate. Ignore
        productivity of the building.

        Returns:
            float: The rate multiplier of the recipe used
        """
        purity_factor = game.PURITY_DURATION_FACTORS[self.purity]
        return super().get_potential_rate() * purity_factor

    def get_problems(self) -> List[str]:
        # TODO: comment in and filter problems if power connection check is implemented
        # probems = super().get_problems()
        return []
        
    # 100% productive even when no monitor is enabled
    def get_productivity(self) -> float:
        return 1.0

    @classmethod
    def get_kwargs(cls, obj: dict, components: Dict[str,dict]) -> dict:
        kwargs = super().get_kwargs(obj, components)
        kwargs['current_recipe_name'] = 'Recipe_GeneratorGeoThermalPower_C'
        kwargs['resource_node_unique_name'] = obj['properties']['mExtractableResource']['path_name'].split('PersistentLevel.')[-1]
        return kwargs


def extract_item_amounts(item_amount_elems: List[dict]) -> ItemValues:
    item_amounts = ItemValues()
    for item in item_amount_elems:
        item_name = item['prop']['path_name'].split('.')[-1]
        amount = item['properties']['Amount']['value']
        item_amounts[item_name] = amount
    return item_amounts


def extract_paid_off_schematics(paid_offs: Iterable[dict]) -> Dict[str, ItemValues]:
    """
    Extract the item amounts paid off for each schematics

    Args:
        paid_offs (List[dict]): Elements from mPaidOffSchematic

    Returns:
        Dict[str, Dict[str, int]]: Mapping from schematics name to paid off item amount
    """
    payoffs = dict()
    for elem in paid_offs:
        schematic_name = elem['prop']['path_name'].split('.')[-1]
        item_amounts = extract_item_amounts(elem['properties']['ItemCost']['elements'])
        payoffs[schematic_name] = item_amounts
    return payoffs


class SchematicManager(Actor):

    def __init__(self, *, purchased_schematics: SchematicFlags=SchematicFlags(),
                 active_schematic: Union[str, None]=None,
                 costs_paid_off: Dict[str, ItemValues]=dict(),
                 **kwargs) -> None:
        """
        Create a SchematicManager object

        Args:
            purchased_schematics (SchematicFlags): All purchased schematics. Defaults to none.
            active_schematic (Union[str, None]): If specified this is the current goal. Defaults to None.
            costs_paid_off (Dict[str, ItemAmounts]): Mapping from schematic name to 
                payoff state as item amount dict. Defaults to dict().
        """
        super().__init__(**kwargs)
        self.purchased_schematics = purchased_schematics
        self.active_schematic = active_schematic
        self.costs_paid_off = costs_paid_off

    def has_active_schematic(self) -> bool:
        return not self.active_schematic is None

    @classmethod
    def get_kwargs(cls, obj: dict, components: Dict[str,dict]) -> dict:
        kwargs = super().get_kwargs(obj, components)
        prop = obj['properties'] 
        if 'mPurchasedSchematics' in prop:
            kwargs['purchased_schematics'] = SchematicFlags([
                elem['path_name'].split('.')[-1]
                for elem in prop['mPurchasedSchematics']['elements']
            ])
        if 'mPaidOffSchematic' in prop:
            paid_offs = prop['mPaidOffSchematic']['elements']
            kwargs['costs_paid_off'] = extract_paid_off_schematics(paid_offs)
        if 'mActiveSchematic' in prop:
            kwargs['active_schematic'] = prop['mActiveSchematic']['path_name'].split('.')[-1]
        return kwargs


class GamePhaseManager(Actor):

    def __init__(self, *, active_phase: Union[str, None],
                 costs_paid_off: ItemValues=ItemValues(),
                 **kwargs) -> None:
        """
        Create a GamePhaseManager object

        Args:
            active_phase (Union[str, None]):
            costs_paid_off (Dict[str, int]): Item amount. Defaults to dict().
        """
        super().__init__(**kwargs)
        self.active_phase = active_phase
        self.costs_paid_off = costs_paid_off

    def has_active_phase(self) -> bool:
        return not self.active_phase is None

    @classmethod
    def get_kwargs(cls, obj: dict, components: Dict[str,dict]) -> dict:
        kwargs = super().get_kwargs(obj, components)
        prop = obj['properties']
        if 'mTargetGamePhase' in prop:
            active_phase_name = prop['mTargetGamePhase']['path_name'].split('.')[-1]
            if not active_phase_name.endswith('_C'):
                active_phase_name = active_phase_name + '_C'
            kwargs['active_phase'] = active_phase_name
        else:
            kwargs['active_phase'] = None
        if 'mTargetGamePhasePaidOffCosts' in prop:
            item_amount_elems = prop['mTargetGamePhasePaidOffCosts']['elements']
            kwargs['costs_paid_off'] = extract_item_amounts(item_amount_elems)
        return kwargs


class InventoryMixin:

    def __init__(self, inventory_stacks: Iterable[ItemStack]) -> None:
        self.inventory_stacks = list(inventory_stacks)

    def get_items(self) -> ItemValues:
        """
        Return the items in the inventory. Solid items are given in number,
        liquid items are given in full liters.

        Returns:
            ItemAmounts: Amount of items by item name
        """
        item_amounts = ItemValues()
        for stack in self.inventory_stacks:
            if stack.is_empty():
                continue
            item_amounts += ItemValues({stack.item_name: stack.amount})
        return item_amounts


class Player(Actor, InventoryMixin):

    def __init__(self, *, transform: tuple,
                 inventory_stacks: List[ItemStack], **kwargs) -> None:
        """
        Create a player.

        Args:
            transform (tuple): position (x,y,z) and orientation (x,y,z,w)
            inventory_stacks (List[ItemStack]): Items the player is possessing
            in its inventory. This is not including the body slots.
        """
        super().__init__(**kwargs)
        InventoryMixin.__init__(self, inventory_stacks)
        self.transform = transform

    def get_map_position(self) -> Tuple[float]:
        return (
            self.transform[0] / 100.0,
            self.transform[1] / 100.0,
            self.transform[2] / 100.0
        )

    @classmethod
    def get_kwargs(cls, obj: dict, components: Dict[str,dict]) -> dict:
        kwargs = super().get_kwargs(obj, components)
        transform = (
            obj["pos_x"],
            obj["pos_y"],
            obj["pos_z"],
            obj["rot_x"],
            obj["rot_y"],
            obj["rot_z"],
            obj["rot_w"],
        )
        kwargs['transform'] = transform
        prop = obj['properties']
        inventory_component = components[prop['mInventory']['path_name']]
        kwargs['inventory_stacks'] = create_inventory_stacks(inventory_component)
        return kwargs


def create_central_storage_stack(element: dict) -> ItemStack:
    item_name = element['prop']['path_name'].split('.')[-1]
    amount = element['properties']['Amount']['value']
    # capacity is set later
    return ItemStack(item_name, amount, capacity=amount)


def deduce_central_storage_stack_count(stacks: List[ItemStack]) -> int:
    if not stacks:
        return 0
    return max(
        math.ceil(stack.amount / game.ITEMS[stack.item_name]['stackSize'])
        for stack in stacks
    )


def create_central_storage_stacks(elements: List[dict]) -> List[ItemStack]:
    stored_items = [
        create_central_storage_stack(elem)
        for elem in elements
    ]
    deduced_stack_count = deduce_central_storage_stack_count(stored_items)
    for stack in stored_items:
        stack.capacity = game.ITEMS[stack.item_name]['stackSize'] * deduced_stack_count
    return stored_items


class CentralStorage(Actor, InventoryMixin):

    def __init__(self, *, transform: tuple,
                 inventory_stacks: List[ItemStack], **kwargs):
        """
        Create a dimensional depot

        Args:
            transform (tuple): position (x,y,z) and orientation (x,y,z,w)
            inventory_stacks (List[ItemStack]): Items the player is possessing
            in the dimensional depot.
        """
        super().__init__(**kwargs)
        InventoryMixin.__init__(self, inventory_stacks)
        self.transform = transform

    @classmethod
    def get_kwargs(cls, obj: dict, components: Dict[str,dict]) -> dict:
        kwargs = super().get_kwargs(obj, components)
        transform = (
            obj["pos_x"],
            obj["pos_y"],
            obj["pos_z"],
            obj["rot_x"],
            obj["rot_y"],
            obj["rot_z"],
            obj["rot_w"],
        )
        kwargs['transform'] = transform
        kwargs['inventory_stacks'] = create_central_storage_stacks(
            obj['properties'].get('mStoredItems', {'elements': []})['elements']
        )
        return kwargs


class World:

    def __init__(self, actors: List[Actor]) -> None:
        self.actors = actors

    def get_factories(self) -> List[Factory]:
        return [actor for actor in self.actors if isinstance(actor, Factory)]
    
    def get_schematic_manager(self) -> SchematicManager:
        selection = [actor for actor in self.actors if isinstance(actor, SchematicManager)]
        if len(selection) != 1:
            names = {actor.instance_name for actor in selection}
            raise ValueError('Expect one schematic manager instance. Got ' + str(names))
        return selection[0]
    
    def get_game_phase_manager(self) -> GamePhaseManager:
        selection = [actor for actor in self.actors if isinstance(actor, GamePhaseManager)]
        if len(selection) != 1:
            names = {actor.instance_name for actor in selection}
            raise ValueError('Expect one game phase manager instance. Got ' + str(names))
        return selection[0]
    
    def get_player(self) -> Player:
        selection = [actor for actor in self.actors if isinstance(actor, Player)]
        if len(selection) != 1:
            names = {actor.instance_name for actor in selection}
            raise ValueError('Expect one player instance. Got ' + str(names))
        return selection[0]
    
    def get_central_storage(self) -> CentralStorage:
        selection = [actor for actor in self.actors if isinstance(actor, CentralStorage)]
        if len(selection) != 1:
            names = {actor.instance_name for actor in selection}
            raise ValueError('Expect one central storage instance. Got ' + str(names))
        return selection[0]

    def get_active_recipes(self, ignore_productivity=True) -> RecipeValues:
        """
        Get the amount of automated recipe in the world. If ignore_productivity
        is True only consider the clock rate. Otherwise also account for the
        productivity.

        Args:
            effective (bool, optional): Whether to ignore the productivity.
            Defaults to False.

        Returns:
            Dict[str, float: Amount of automated recipes active
        """ 
        recipe_amounts = RecipeValues(omega=game.RECIPE_NAMES_AUTOMATED)
        for factory in self.get_factories():
            recipe_name = factory.current_recipe_name
            if not recipe_name in game.RECIPE_NAMES_AUTOMATED:
                if recipe_name:
                    raise ValueError('Unknown recipe:', recipe_name)
                continue
            if factory.is_production_paused:
                continue
            if ignore_productivity:
                rate = factory.get_potential_rate()
            else:
                rate = factory.get_effective_rate()
            recipe_amounts[recipe_name] += rate
        return recipe_amounts
    
    def get_occupied_resource_node_unique_names(self) -> Set[str]:
        """Get the unique names of all occupied resource nodes, i.g. resource
        nodes, where a fracking building is placed.

        Returns:
            Set[str]: Names of the occupied resource names
        """
        return {
            x.resource_node_unique_name
            for x in self.get_factories()
            if isinstance(x, NodeMixin)
        }
    
    def get_occupied_resource_nodes(self) -> ResourceNodeValues:
        """
        Get the amount of resource nodes occupied for each resource node type.
        The amount is defined as the sum over the occupation ratios over all nodes.

        Returns:
            ResourceNodeAmounts: Resource node amounts that are occupied
        """
        res_node_amounts = ResourceNodeValues()
        for extractor in self.get_factories():
            if not isinstance(extractor, NodeMixin):
                continue
            if 'FGWaterVolume' in extractor.resource_node_unique_name:
                continue
            # TODO: Let overclocking not turn occupancy higher than the correct value
            extractor_purity = game.PURITY_DURATION_FACTORS[extractor.purity]
            clock_rate = extractor.get_potential_rate() / extractor_purity
            unique_resource_node = game.UNIQUE_NODES[extractor.resource_node_unique_name]
            node_purity = game.PURITY_DURATION_FACTORS[unique_resource_node['purity']]
            resource_node_name = game.get_resource_node_name(
                unique_resource_node['resource'],
                unique_resource_node['fracking']
            )
            res_node_amounts[resource_node_name] += clock_rate * node_purity
        return res_node_amounts


BUILD2CLASS = {
    # Fracking
    '/Game/FactoryGame/Buildable/Factory/MinerMK1/Build_MinerMk1.Build_MinerMk1_C': 
        FrackingBuilding,
    '/Game/FactoryGame/Buildable/Factory/MinerMk2/Build_MinerMk2.Build_MinerMk2_C':
        FrackingBuilding,
    '/Game/FactoryGame/Buildable/Factory/MinerMK3/Build_MinerMk3.Build_MinerMk3_C':
        FrackingBuilding,
    '/Game/FactoryGame/Buildable/Factory/OilPump/Build_OilPump.Build_OilPump_C':
        FrackingBuilding,
    '/Game/FactoryGame/Buildable/Factory/WaterPump/Build_WaterPump.Build_WaterPump_C':
        FrackingBuilding,
    '/Game/FactoryGame/Buildable/Factory/FrackingExtractor/Build_FrackingExtractor.Build_FrackingExtractor_C':
        FrackingBuilding,

    # Manufacturing
    '/Game/FactoryGame/Buildable/Factory/SmelterMk1/Build_SmelterMk1.Build_SmelterMk1_C':
        ManufacturingBuilding,
    '/Game/FactoryGame/Buildable/Factory/FoundryMk1/Build_FoundryMk1.Build_FoundryMk1_C':
        ManufacturingBuilding,
    '/Game/FactoryGame/Buildable/Factory/ConstructorMk1/Build_ConstructorMk1.Build_ConstructorMk1_C':
        ManufacturingBuilding,
    '/Game/FactoryGame/Buildable/Factory/AssemblerMk1/Build_AssemblerMk1.Build_AssemblerMk1_C':
        ManufacturingBuilding,
    '/Game/FactoryGame/Buildable/Factory/ManufacturerMk1/Build_ManufacturerMk1.Build_ManufacturerMk1_C':
        ManufacturingBuilding,
    '/Game/FactoryGame/Buildable/Factory/OilRefinery/Build_OilRefinery.Build_OilRefinery_C':
        ManufacturingBuilding,
    '/Game/FactoryGame/Buildable/Factory/Blender/Build_Blender.Build_Blender_C':
        ManufacturingBuilding,
    '/Game/FactoryGame/Buildable/Factory/Packager/Build_Packager.Build_Packager_C':
        ManufacturingBuilding,
    '/Game/FactoryGame/Buildable/Factory/HadronCollider/Build_HadronCollider.Build_HadronCollider_C':
        ManufacturingBuilding,
    '/Game/FactoryGame/Buildable/Factory/QuantumEncoder/Build_QuantumEncoder.Build_QuantumEncoder_C':
        ManufacturingBuilding,
    '/Game/FactoryGame/Buildable/Factory/Converter/Build_Converter.Build_Converter_C':
        ManufacturingBuilding,

    # Generators
    '/Game/FactoryGame/Buildable/Factory/GeneratorBiomass/Build_GeneratorBiomass_Automated.Build_GeneratorBiomass_Automated_C'
        : GeneratorBuilding,
    '/Game/FactoryGame/Buildable/Factory/GeneratorBiomass/Build_GeneratorIntegratedBiomass.Build_GeneratorIntegratedBiomass_C'
        : GeneratorBuilding,
    '/Game/FactoryGame/Buildable/Factory/GeneratorCoal/Build_GeneratorCoal.Build_GeneratorCoal_C'
        : GeneratorBuilding,
    '/Game/FactoryGame/Buildable/Factory/GeneratorFuel/Build_GeneratorFuel.Build_GeneratorFuel_C'
        : GeneratorBuilding,
    '/Game/FactoryGame/Buildable/Factory/GeneratorNuclear/Build_GeneratorNuclear.Build_GeneratorNuclear_C'
        : GeneratorBuilding,
    '/Game/FactoryGame/Buildable/Factory/GeneratorGeoThermal/Build_GeneratorGeoThermal.Build_GeneratorGeoThermal_C'
        : ThermalGenerator,
    '/Game/FactoryGame/Buildable/Factory/AlienPower/Build_AlienPowerBuilding.Build_AlienPowerBuilding_C'
        : AlienPowerBuilding,

    # game progression
    '/Game/FactoryGame/Schematics/Progression/BP_SchematicManager.BP_SchematicManager_C':
        SchematicManager,
    '/Game/FactoryGame/Schematics/Progression/BP_GamePhaseManager.BP_GamePhaseManager_C':
        GamePhaseManager,

    # Characters
    '/Game/FactoryGame/Character/Player/Char_Player.Char_Player_C':
        Player,

    # Other
    '/Script/FactoryGame.FGCentralStorageSubsystem':
        CentralStorage,
}


def instantiate_world(objects: List[dict]) -> World:
    # assign components
    components = dict()
    for o in objects:
        if o['object_type'] == COMPONENT_TYPE:
            components[o['instance_name']] = o
    
    # create actors
    actors = []
    missed_types = set()
    for o in objects:
        if not o['type_path'] in BUILD2CLASS:
            missed_types.add(o['type_path'])
            continue
        actor_components = {
            component_ref['path_name']: components[component_ref['path_name']]
            for component_ref in o['components']
        }
        cls = BUILD2CLASS[o['type_path']]
        try:
            actor = cls.create(o, actor_components)
        except Exception as e:
            from pprint import pprint
            pprint(o)
            raise e
        actors.append(actor)

    # guide implementation
    facility_names = set(game.BUILDINGS)
    for type_path in missed_types:
        if any(game.get_bare_name(facility_name) in type_path for facility_name in facility_names):
            print('WARNING Missed types:', type_path)

    return World(actors=actors)
