import importlib
import pkgutil

from .base import BaseArchiveRecipe

for (module_loader, name, ispkg) in pkgutil.iter_modules(["archives"]):
    importlib.import_module('.' + name, __package__)

all_recipes = {cls for cls in BaseArchiveRecipe.__subclasses__()}
