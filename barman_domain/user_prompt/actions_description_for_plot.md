You are given:
1) A system prompt describing a planning domain for a cocktail workstation (objects/resources, actions, and directives).
2) A JSON list of the RESOURCES present in the scene (authoritative for tool types and ingredient ids).
3) A JSON list of the ABSTRACT ACTIONS (authoritative for base action names and parameter roles).

RESOURCES (authoritative):
<PASTE_RESOURCES_JSON_HERE>

ABSTRACT ACTIONS (authoritative):
<PASTE_ACTIONS_JSON_HERE>

Task:
Generate the complete list of concrete action variants and output them as structured objects. Each variant must include:
- a unique variant id (string)
- the abstract action type it comes from
- the ordered list of object/type tokens referenced by that variant

Output format:
Return ONLY a JSON array of objects (no extra text), exactly in this structure:

[
  {
    "id": "<variant_id>",
    "action": "<abstract_action_name>",
    "objects": ["<token1>", "<token2>", ...]
  }
]

How to generate variants (generic procedure):
1) From RESOURCES, extract:
   - tool types (physical tools)
   - ingredient identifiers (non-tool resources where id == type, e.g., ingredient1, ingredient2, ...)
2) From ABSTRACT ACTIONS, extract the base action names and their parameter roles.
3) For each abstract action, infer which tool types it can apply to based on the system prompt semantics and parameter roles. Create one variant per applicable tool-type combination.
4) Expand across ingredient ids ONLY when the action semantics requires distinguishing the ingredient to form different variants.
5) For transfer actions, if the domain semantics indicates that multiple ingredients may be transferred but the transfer operation itself does not require specifying which ingredient in the variant name, then DO NOT expand by ingredient; represent a single generic transfer variant per source/target tool-type pair.

IMPORTANT: ingredient abstraction for transfer variants
- If a transfer action can move any of multiple ingredients but the system prompt does not require identifying which ingredient to describe the transfer operation at the variant level,
  then produce ONLY a generic transfer variant name without ingredient tokens (e.g., pour-shot-to-shaker), and do NOT include any ingredient in the "objects" list for that variant.

Variant id naming rules (consistent and deterministic):
- Use lowercase kebab-case.
- Do NOT use natural-language articles or generic phrases in ids (no "a-", "an-", "the-", etc.).
- Every token used in a variant id MUST be taken from:
  - an abstract action name (from ABSTRACT ACTIONS), and/or
  - a tool type token (from RESOURCES "type"), and/or
  - a domain-defined product/content label (e.g., "cocktail") ONLY if explicitly needed to distinguish different transfer modes.
- Do NOT include specific ingredient ids in transfer variant ids unless ingredient-specific variants are explicitly required by the domain.

Base id structure:
- Start every id with the abstract action name.

Single-tool variants:
- If an action applies to exactly one tool parameter, set:
  id = "<action>-<tool_type>"
  objects = ["<tool_type>"]

Ingredient-specific variants (non-transfer):
- If an action applies to one tool and semantically uses/introduces a specific ingredient, set:
  id = "<action>-<tool_type>-with-<ingredient_id>"
  objects = ["<tool_type>", "<ingredient_id>"]

Transfer variants (source/target):
- If an action transfers between two tools, ALWAYS include BOTH endpoints:
  id = "<action>-<source_tool_type>-to-<target_tool_type>"
  objects = ["<source_tool_type>", "<target_tool_type>"]

Constraints:
- Do NOT invent tools or action modes not supported by RESOURCES, ABSTRACT ACTIONS, and the system prompt.
- Generate ALL valid variants implied by the inputs.
- Return ONLY the array of objects in the required schema.

Deterministic ordering:
- Order variants by the order of actions in ABSTRACT ACTIONS.
- Within an action, order by tool types (lexicographic).