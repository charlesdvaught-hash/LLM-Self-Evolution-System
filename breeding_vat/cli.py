#!/usr/bin/env python3
"""
CLI for managing and executing breeding vat recipes.

Quick commands:
  python -m breeding_vat.cli recipes --list
  python -m breeding_vat.cli recipes --execute reasoning_fusion_v1
  python -m breeding_vat.cli recipes --validate reasoning_fusion_v1
  python -m breeding_vat.cli recipes --describe reasoning_fusion_v1
"""

import argparse
import json
import sys
from breeding_vat.modules.recipe_executor import RecipeExecutor


def cmd_list_recipes(executor: RecipeExecutor):
    """List all saved recipes."""
    recipes = executor.list_recipes()
    
    if not recipes:
        print("No recipes saved yet.")
        return
    
    print(f"\n📋 Saved Recipes ({len(recipes)})\n")
    
    for recipe_name in recipes:
        recipe = executor.load_recipe(recipe_name)
        meta = recipe.get("metadata", {})
        desc = meta.get("description", "(no description)")
        print(f"  {recipe_name}")
        print(f"    → {desc}\n")


def cmd_validate_recipe(executor: RecipeExecutor, recipe_name: str):
    """Validate a recipe."""
    recipe = executor.load_recipe(recipe_name)
    result = executor.validate(recipe)
    
    if result.valid:
        print(f"✅ Recipe is valid: {recipe_name}\n")
    else:
        print(f"❌ Recipe has errors:\n")
        for error in result.errors:
            print(f"  ✗ {error}")
    
    if result.warnings:
        print(f"\n⚠️ Warnings:\n")
        for warning in result.warnings:
            print(f"  ⚠ {warning}")


def cmd_describe_recipe(executor: RecipeExecutor, recipe_name: str):
    """Print a human-readable description of a recipe."""
    recipe = executor.load_recipe(recipe_name)
    print(executor.describe(recipe))


def cmd_execute_recipe(executor: RecipeExecutor, recipe_name: str):
    """
    Execute a recipe (print configuration for Streamlit UI to consume).
    
    In production, the UI would call build_evolution_config() and pass to EvolutionEngine.
    For now, we just print the config.
    """
    recipe = executor.load_recipe(recipe_name)
    result = executor.validate(recipe)
    
    if not result.valid:
        print(f"❌ Recipe has validation errors. Fix before executing:\n")
        for error in result.errors:
            print(f"  ✗ {error}")
        sys.exit(1)
    
    print(f"▶️ Executing recipe: {recipe_name}\n")
    
    evo_config = executor.build_evolution_config(recipe)
    print(f"Evolution config:\n{json.dumps(evo_config, indent=2)}\n")
    
    ft_config = executor.build_finetuning_config(recipe)
    if ft_config:
        print(f"Fine-tuning config:\n{json.dumps(ft_config, indent=2)}\n")
    else:
        print("Fine-tuning: disabled\n")
    
    assay_config = executor.build_assay_config(recipe)
    if assay_config:
        print(f"ASSAY config:\n{json.dumps(assay_config, indent=2)}\n")
    else:
        print("ASSAY: disabled\n")
    
    print("\n✅ Recipe ready for execution.")
    print("   (Implement in UI: pass evo_config to EvolutionEngine)")


def main():
    parser = argparse.ArgumentParser(
        description="Breeding Vat Recipe Manager",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m breeding_vat.cli recipes --list
  python -m breeding_vat.cli recipes --validate reasoning_fusion_v1
  python -m breeding_vat.cli recipes --describe reasoning_fusion_v1
  python -m breeding_vat.cli recipes --execute reasoning_fusion_v1
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    recipes_parser = subparsers.add_parser("recipes", help="Manage recipes")
    recipes_parser.add_argument("--list", action="store_true", help="List all recipes")
    recipes_parser.add_argument("--validate", metavar="NAME", help="Validate a recipe")
    recipes_parser.add_argument("--describe", metavar="NAME", help="Describe a recipe")
    recipes_parser.add_argument("--execute", metavar="NAME", help="Execute a recipe (show config)")
    
    args = parser.parse_args()
    
    if args.command == "recipes":
        executor = RecipeExecutor()
        
        if args.list:
            cmd_list_recipes(executor)
        elif args.validate:
            cmd_validate_recipe(executor, args.validate)
        elif args.describe:
            cmd_describe_recipe(executor, args.describe)
        elif args.execute:
            cmd_execute_recipe(executor, args.execute)
        else:
            recipes_parser.print_help()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
