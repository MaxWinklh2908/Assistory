# Buildings
## Power consumption
- positive to buildings that consume energy
- negative for generators

# Resource nodes
## Purity
Purity is fixed for every node in the game and can be impure, normal and pure. The purity is only defined ingame and can not be extracted from the docs of save file. To correctly estimate the extraction rates of from save files, ensure the resource nodes/wells in use are correctly defined in the [extension_data](../extension_data.json).

### Resource node data check
To check correct definition, upload the save file to the interactive map of [satisfactory-calculator](https://satisfactory-calculator.com/en/interactive-map) and retrieve the resource name for every extractor (miners, fracking extractor, oil pump, geotermal generators):
- Miner (Build_MinerMk1/2/3_C): Right Click on building > **Advanced_Debug** > **properties** > **mExtractableResource** > **value** and note the path name, e.g. `BP_ResourceNode115`
- Oil Extractor (Build_OilPump_C): Right Click on building > **Advanced_Debug** > **properties** > **mExtractableResource** > **value** and note the path name, e.g. `BP_ResourceNode460`
- Resource Well Extractor (Build_FrackingExtractor_C): Right Click on building > **Advanced_Debug** > **properties** > **mExtractableResource** > **value** and note the path name, e.g. `BP_FrackingSatellite36`
- Geotermal Generator (Build_GeneratorGeoThermal_C): Right Click on building > **Advanced_Debug** > **properties** > **mExtractableResource** > **value** and note the path name, e.g. `BP_ResourceNodeGeyser11_3803`

Next, lookup all the noted resource node names in the [extension_data](../extension_data.json). If an entry exists for the name, the resource node is contained. Otherwise, the data can be updated, by replacing an entry containing `Mock` with the matching ``purity`` and ``resource`` type. **Oil extractors** (oil pump) are placed on resource nodes. **Resource well extractors** (fracking extractor) are placed on resource wells. `fracking` is only true if the resource is a resource well. For Geotermal generators use `special__power` as resource.

# Fracking
Fracking buildings produce liquid items (including gas).

# Recipes


## Generators
Items can have an energy value. A generator uses items to convert the item energy to electrical power (without loss). Each generator has a fixed output power. The item input rate is matched to provide the required power.

Example: 30MW Biomass Burner, with 180MJ biomass: 180MJ provides 30MJ over 6s (30*6 = 180). Therefore, The biomass Burner needs 10 Biomass per minute.

For each building and each of its fuel items a recipe is added.

## Extraction
Item that are generated without input are extractable (exceptions?). 

For each building and each of its respective resources a recipe is added.

## Handcraft

All resources, flora and fauna can be aquired without buildings. Additionally, the recipes available at the crafting bench or equipement store are handcrafting recipes. These recipes are available under recipes_handcraft.
