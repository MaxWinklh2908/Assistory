import networkx as nx

from assistory import game
from assistory.game import ItemValues, RecipeValues, ItemFlags


def _add_item_flow_edge(
        G: nx.DiGraph,
        item_name: str,
        other_node_name: str,
        flow_other_to_item: float
    ):
    if flow_other_to_item < 0: # ingredient
        u_name = item_name
        v_name = other_node_name
    elif flow_other_to_item > 0: # product
        u_name = other_node_name
        v_name = item_name
    else:
        raise ValueError('Flow can not be zero')

    G.add_edge(
        u_name,
        v_name,
        flow=abs(flow_other_to_item),
        state='liquid' if item_name in game.ITEM_NAMES_LIQUID else 'solid',
        label=str(abs(flow_other_to_item)),
    )


def add_recipe_flow(
        G: nx.DiGraph,
        recipe_amounts: RecipeValues,
        round_digits=4,
        ignore_water=False,
    ) -> ItemFlags:
    """
    A the network of recipes to item balances to a directed graph. The flow is
    always positive and defines consumption/production by direction. Recipe
    nodes are be labelled with the name + (Recipe). Item nodes are labelled
    with the name + (Item). Edges with (rounded) zero flow are not added.

    Args:
        G (nx.DiGraph): Directed graph where to add network
        recipe_amounts (RecipeValues): Nonnegative amounts of recipes
        round_digits (int, optional): Round flow by this precision. Defaults to 4.
        ignore_water (bool, optional): Exclude water flow and it's extraction
            recipes. Defaults to False.
    """
    for recipe_name, amount in recipe_amounts.items():
        if amount < 0:
            raise RuntimeError(f'Invalid (negative) amount of {recipe_name}')

    item_used = ItemFlags()
    for recipe_name, amount in recipe_amounts.items():
        if recipe_amounts[recipe_name] == 0:
            continue
        if ignore_water and (
            recipe_name == 'Recipe_WaterPumpWater_C' or
            recipe_name == 'Recipe_FrackingExtractorWater_C'):
            continue

        G.add_node(
            recipe_name,
            label=game.RECIPES[recipe_name]['name'] + ' (Recipe)',
            amount=amount,
            node_type='recipe',
        )

        recipe_flow = RecipeValues({recipe_name: amount}).get_item_rate_balance()
        recipe_flow = recipe_flow.round(round_digits)
        for item_name, flow in recipe_flow.items():
            if flow == 0:
                continue
            if ignore_water and item_name == 'Desc_Water_C':
                continue

            G.add_node(item_name) # add details later

            _add_item_flow_edge(G, item_name, recipe_name, flow)
            item_used.add(item_name)

    return item_used


def add_base_flow(
        G: nx.DiGraph,
        base_item_rates: ItemValues,
        round_digits=4,
        ignore_water=False,
    ):
    """
    Add the network of base item rates. This introduces additional flow between
    base item nodes and the item nodes. Available base items create a flow to
    the item nodes. Required base items (negative) create a flow from the item
    nodes.

    Args:
        G (nx.DiGraph): Directed graph where to add network
        base_item_rates (ItemValues): Amounts of base item rate
        round_digits (int, optional): Round flow by this precision. Defaults to 4.
        ignore_water (bool, optional): Exclude water flow. Defaults to False.
    """
    item_used = ItemFlags()
    for item_name, flow in base_item_rates.round(round_digits).items():
        if flow == 0:
            continue
        if ignore_water and item_name == 'Desc_Water_C':
            continue

        G.add_node(item_name) # add details later
        G.add_node(
            item_name + '_base',
            label=game.ITEMS[item_name]['name'] + ' (Base)',
            item_rate=flow,
            node_type='base',
        )

        _add_item_flow_edge(G, item_name, item_name + '_base', flow)
        item_used.add(item_name)

    return item_used


def add_item_nodes(
        G: nx.DiGraph,
        items_used: ItemFlags,
        item_rate_balances: ItemValues,
        round_digits=4,
    ):
    """
    Add (or overwrite) item nodes with detailed attributes.

    Args:
        G (nx.DiGraph): Directed graph where to add nodes
        items_used (ItemFlags): Items for which a detailed node should be added
        item_rate_balances (ItemValues): Balance of each item rate
        round_digits (int, optional): Round balance by this precision. Defaults to 4.
    """
    item_rates = item_rate_balances.round(round_digits)
    for item_name in items_used:
        # The nodes exist already but are overwriten with more details
        G.add_node(
            item_name,
            label=game.ITEMS[item_name]['name'] + ' (Item)',
            item_rate_balance=item_rates[item_name],
            node_type='item',
        )


def create_production_graph(
        recipe_amounts: RecipeValues,
        base_item_rates: ItemValues=ItemValues(),
        round_digits=4,
        ignore_water=False,
    ) -> nx.DiGraph:
    """
    Create a directed graph of the item flow. Nodes are item rate balances, recipe
    amounts and base item rates. Item rate balances can be negative, zero or
    positive. Recipe amounts integrate all factories for each recipe into a node.
    Base item rates are a additional rates added to the item rate balances.

    Args:
        recipe_amounts (RecipeValues): Nonnegative amounts of recipes
        base_item_rates (ItemValues): Amounts of base item rate. Defaults to
            all 0.
        round_digits (int, optional): Round flow by this precision. Defaults to 4.
        ignore_water (bool, optional): Exclude water flow and it's extraction
            recipes. Defaults to False.

    Returns:
        nx.DiGraph: Directed graph of the item flow
    """

    G = nx.DiGraph()

    items_used = ItemFlags()
    items_used |= add_recipe_flow(G, recipe_amounts, round_digits, ignore_water)
    items_used |= add_base_flow(G, base_item_rates, round_digits, ignore_water)

    item_rate_balance = recipe_amounts.get_item_rate_balance() + base_item_rates
    add_item_nodes(G, items_used, item_rate_balance, round_digits)

    return G
