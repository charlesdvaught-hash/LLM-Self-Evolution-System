# Research Recipes & Templates

Verified "Presets" and strategy templates from LLM merging research papers.

## 🧪 Template 1: TIES-DARE Hybrid (The "Modern Standard")
- **Method**: DARE with TIES-style trimming.
- **Why**: DARE keeps the variance high, TIES removes interference.
- **Recipe**:
  ```yaml
  merge_method: dare_ties
  base_model: [Select Neutral Base]
  models:
    - model: [Expert A]
      parameters: {weight: 0.5, density: 0.9}
    - model: [Expert B]
      parameters: {weight: 0.5, density: 0.9}
  ```

## 🧪 Template 2: The "Franken-Reasoning" (Layer-wise)
- **Method**: Frankenmerge (FusionBench).
- **Why**: Use logic layers from Parent A and creative layers from Parent B.
- **Recipe**:
  - Layers 0-12: Parent A (Logic)
  - Layers 13-24: Parent B (Creative)
  - Layers 25-32: Parent A (Head)

## 🧪 Template 3: SLERP-Linear "Safety Valve"
- **Method**: SLERP (MergeKit).
- **Why**: Use for interpolating two very similar models (e.g., base and slightly finetuned).
- **Parameters**: `t: 0.5` (perfect midpoint).

## 🧪 Template 4: Task Arithmetic "De-Biasing"
- **Method**: NegMerge.
- **Why**: Subtract a "negative" model (e.g., one with bad formatting or bias).
- **Formula**: `Offspring = PositiveModel - 0.2 * NegativeModel`.

## 🧪 Template 5: MoE "Kitchen Sink"
- **Method**: MOE.
- **Why**: Combine 4+ small models (1B range) into a single 4B MoE.
- **Strategy**:
  - Expert 1: Coding
  - Expert 2: Math
  - Expert 3: Roleplay
  - Expert 4: Chat
