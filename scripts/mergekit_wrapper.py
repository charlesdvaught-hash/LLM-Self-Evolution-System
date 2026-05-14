import sys
import os

# Apply Pydantic/MergeKit compatibility patch
try:
    import torch
    import pydantic
    from mergekit.plan import ConfiguredModuleArchitecture, ConfiguredModelArchitecture

    # We use model_rebuild to resolve ForwardRefs that fail in some environments
    namespace = {"torch": torch}
    ConfiguredModuleArchitecture.model_rebuild(_types_namespace=namespace)
    ConfiguredModelArchitecture.model_rebuild(_types_namespace=namespace)
except (ImportError, AttributeError, Exception) as e:
    # If anything fails during patching, we log and continue
    # as the environment might not actually need the patch
    pass

from mergekit.scripts.run_yaml import main
if __name__ == "__main__":
    # This script acts as a drop-in replacement for the mergekit-yaml CLI
    main()
