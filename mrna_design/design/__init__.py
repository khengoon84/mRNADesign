"""The design module: data contracts (T07), plugins and the registry (T08+).

Imports stay one-way (AD-1): other modules import *this* package; this package
never imports the shell, QC or construct modules.
"""

from mrna_design.design import plugins as plugins
from mrna_design.design import registry as registry
from mrna_design.design.plugins import CONTRACT_VERSION, Capabilities
from mrna_design.design.registry import REGISTRY, Registry

__all__ = ["Capabilities", "CONTRACT_VERSION", "REGISTRY", "Registry", "plugins", "registry"]
