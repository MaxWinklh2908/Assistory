
## Dependency Graph

```mermaid
graph TD
  Item[Item]
  ResourceNode[ResourceNode]
  Building[Building]
  Recipe[Recipe]
  Schematic[Schematic]

  Building --> Item
  Building --> ResourceNode

  Recipe --> Item
  Recipe --> Building
  Recipe --> ResourceNode

  Schematic --> Item
  Schematic --> Building
  Schematic --> Recipe
```