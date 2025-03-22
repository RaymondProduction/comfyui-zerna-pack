"""
@author: Raymond
@title: Zerna Pack
@nickname: Zerna Pack
@description: A set of nodes for batch processing of text and images.
@version: 0.0.1
"""

import importlib       # ✅ Standard library
import logging         # ✅ Standard library

version_code = [0, 0, 1]
version_str = f"V{version_code[0]}.{version_code[1]}" + (f'.{version_code[2]}' if len(version_code) > 2 else '')
logging.info(f"### Loading: ComfyUI-Zerna-Pack ({version_str})")

node_list = [
    "prompt_generators"
]

NODE_CLASS_MAPPINGS = {}
NODE_DISPLAY_NAME_MAPPINGS = {}

for module_name in node_list:
    imported_module = importlib.import_module(".zerna.{}".format(module_name), __name__)

    NODE_CLASS_MAPPINGS = {**NODE_CLASS_MAPPINGS, **imported_module.NODE_CLASS_MAPPINGS}
    NODE_DISPLAY_NAME_MAPPINGS = {**NODE_DISPLAY_NAME_MAPPINGS, **imported_module.NODE_DISPLAY_NAME_MAPPINGS}

WEB_DIRECTORY = "./js"
__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS", "WEB_DIRECTORY"]

try:
    import cm_global
    cm_global.register_extension('ComfyUI-Zerna-Pack',
                                 {'version': version_code,
                                  'name': 'Zerna Pack',
                                  'nodes': set(NODE_CLASS_MAPPINGS.keys()),
                                  'description': 'A set of nodes for batch processing of text and images.', })
except:
    pass
