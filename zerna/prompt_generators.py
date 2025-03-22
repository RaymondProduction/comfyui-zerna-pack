from comfy.comfy_types import IO  # 🔶 Part of ComfyUI core, not installed via pip
import folder_paths               # 🔶 Provided by ComfyUI (not a standard library)

import os      # ✅ Standard library
import logging # ✅ Standard library


def add_folder_path_and_extensions(folder_name, full_folder_paths, extensions):
    for full_folder_path in full_folder_paths:
        folder_paths.add_model_folder_path(folder_name, full_folder_path)
    if folder_name in folder_paths.folder_names_and_paths:
        current_paths, current_extensions = folder_paths.folder_names_and_paths[folder_name]
        updated_extensions = current_extensions | extensions
        folder_paths.folder_names_and_paths[folder_name] = (current_paths, updated_extensions)
    else:
        folder_paths.folder_names_and_paths[folder_name] = (full_folder_paths, extensions)

model_path = folder_paths.models_dir
add_folder_path_and_extensions("zerna_prompts", [os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "prompts"))], {'.txt'})

def process_prompts(prompt_text, prompt_data):
    prompts = []  # Array to store results

    # Check if [X] is in prompt_text
    if "[X]" in prompt_text:
        for line in prompt_data.splitlines():
            logging.info(f"process_prompts line: {line}")
            # Replace [X] with the current line
            processed_text = prompt_text.replace("[X]", line.strip())
            # Add the result to the prompts array
            prompts.append((processed_text, "man", "unknown name"))  # None for negative
            logging.info(f"process_prompts processed_text: {processed_text}")
    else:
        # If [X] is not found, add the original prompt_text
        prompts.append((prompt_text, "man", "unknown name"))

    return prompts

# model_path = folder_paths.models_dir
# utils.add_folder_path_and_extensions("zerna_prompts", [os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "prompts"))], {'.txt'})

class DynamicPromptInjector:
    @classmethod
    def INPUT_TYPES(cls):
        prompt_files = []
        try:
            prompts_paths = folder_paths.get_folder_paths('zerna_prompts')
            for prompts_path in prompts_paths:
                for root, dirs, files in os.walk(prompts_path):
                    for file in files:
                        if file.endswith(".txt"):
                            file_path = os.path.join(root, file)
                            rel_path = os.path.relpath(file_path, prompts_path)
                            prompt_files.append(rel_path)
        except Exception:
            prompt_files = []

        logging.info(f"INPUT_TYPES prompt_files: {prompt_files}")

        return {"required": {
                    "prompt_text": (IO.STRING, {"multiline": True, "dynamicPrompts": True, "tooltip": "The text to be xxxx."}),
                    "prompt_file": (prompt_files,)
                    },
                "optional": {
                    "reload": ("BOOLEAN", { "default": False, "label_on": "if file changed", "label_off": "if value changed"}),
                    "load_cap": ("INT", {"default": 0, "min": 0, "step": 1, "advanced": True, "tooltip": "The amount of prompts to load at once:\n0: Load all\n1 or higher: Load a specified number"}),
                    "start_index": ("INT", {"default": 0, "min": -1, "step": 1, "max": 0xffffffffffffffff, "advanced": True, "tooltip": "Starting index for loading prompts:\n-1: The last prompt\n0 or higher: Load from the specified index"}),
                    }
                }

    RETURN_TYPES = ("ZIPPED_PROMPT", "INT", "INT")
    RETURN_NAMES = ("zipped_prompt", "count", "remaining_count")
    OUTPUT_IS_LIST = (True, False, False)

    FUNCTION = "doit"

    CATEGORY = "ZernaPack/Prompt"

    @staticmethod
    def IS_CHANGED(prompt_text, prompt_file, reload=False, load_cap=0, start_index=-1):
        print("RAYMOND IS_CHANGED")
        logging.info(f"IS_CHANGED prompt_text: {prompt_text}")
        logging.info(f"IS_CHANGED prompt_files: {prompt_file}")
        return prompt_file, load_cap, start_index

    @staticmethod
    def doit(prompt_text, prompt_file, reload=False, load_cap=0, start_index=-1):
        logging.info(f"doit prompt_text: {prompt_text}")
        logging.info(f"doit prompt_dir: {prompt_file}")
        matched_path = None
        for d in folder_paths.get_folder_paths('zerna_prompts'):
            matched_path = os.path.join(d, prompt_file)
            if os.path.exists(matched_path):
                break
            else:
                matched_path = None
        
        logging.info(f"doit matched_path: {matched_path}")
        if matched_path:
            logging.info(f"[Inspire Pack] LoadPromptsFromFile: file found '{prompt_file}'")
        else:
            logging.warning(f"[Inspire Pack] LoadPromptsFromFile: file not found '{prompt_file}'")

        with open(matched_path, "r", encoding="utf-8") as file:
            prompt_data = file.read()
        logging.info(f"doit prompt_data: {prompt_data}")
        logging.info(f"doit prompt_text: {prompt_text}")
        return process_prompts(prompt_text, prompt_data), 1, 1



NODE_CLASS_MAPPINGS = {
    "DynamicPromptInjector //Zerna Pack": DynamicPromptInjector
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "DynamicPromptInjector //Zerna Pack": "Dynamic Prompt Injector (Zerna Pack)",
}