from tkinter import Image
from comfy.comfy_types import IO  # 🔶 Part of ComfyUI core, not installed via pip
import folder_paths               # 🔶 Provided by ComfyUI (not a standard library)
from PIL import Image             # 🔶 Part of ComfyUI core, not installed via pip
import numpy as np                # 🔶 Part of ComfyUI core, not installed via pip

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

add_folder_path_and_extensions("zerna_prompts", [os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "prompts"))], {'.txt'})

def init_prompt_files_list():
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
    
    return prompt_files

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

def process_prompts_encode(clip, prompt_text, prompt_data):
    positiveEncodes = []  # Array to store results
    negativeEncodes = []  # Array to store results

    # Check if [X] is in prompt_text
    if "[X]" in prompt_text:
        for line in prompt_data.splitlines():
            logging.info(f"process_prompts line: {line}")
            # Replace [X] with the current line
            processed_text = prompt_text.replace("[X]", line.strip())
            positive = tokenize_and_encode(clip, processed_text)
            negative = tokenize_and_encode(clip, "man")

            positiveEncodes.append(positive)
            negativeEncodes.append(negative)
            
            # Ensure both positive and negative are valid
            if positive is None or negative is None:
                logging.error("Tokenization or encoding failed.")
                continue
            
            # Add the result to the encodes array
            logging.info(f"process_prompts processed_text: {processed_text}")
    else:
        # If [X] is not found, add the original prompt_text
        positive = tokenize_and_encode(clip, prompt_text)
        negative = tokenize_and_encode(clip, "man")

        positiveEncodes.append(positive)
        negativeEncodes.append(negative)
    
    if positive is None or negative is None:
        logging.error("Tokenization or encoding failed.")
    else:
        return positiveEncodes,negativeEncodes

def read_file_prompt_data(prompt_file):
        matched_path = None
        for d in folder_paths.get_folder_paths('zerna_prompts'):
            matched_path = os.path.join(d, prompt_file)
            if os.path.exists(matched_path):
                break
            else:
                matched_path = None
        
        logging.info(f"doit matched_path: {matched_path}")
        if matched_path:
            logging.info(f"[Zerna Pack] LoadPromptsFromFile: file found '{prompt_file}'")
        else:
            logging.warning(f"[Zerna Pack] LoadPromptsFromFile: file not found '{prompt_file}'")

        with open(matched_path, "r", encoding="utf-8") as file:
             prompt_data = file.read()
    
        return prompt_data

def tokenize_and_encode(clip, text):
    tokens = clip.tokenize(text)
    return clip.encode_from_tokens_scheduled(tokens)

class DynamicPromptInjector:
    @classmethod
    def INPUT_TYPES(cls):
        prompt_files = init_prompt_files_list()

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

    CATEGORY = "ZernaPack/PromptGnerators"

    @staticmethod
    def IS_CHANGED(prompt_text, prompt_file, reload=False, load_cap=0, start_index=-1):
        logging.info(f"IS_CHANGED prompt_text: {prompt_text}")
        logging.info(f"IS_CHANGED prompt_files: {prompt_file}")
        return prompt_file, load_cap, start_index

    @staticmethod
    def doit(prompt_text, prompt_file, reload=False, load_cap=0, start_index=-1):
        prompt_data = read_file_prompt_data(prompt_file)
        return process_prompts(prompt_text, prompt_data), 1, 1

class CLIPDynamicPromptEncoder():
    @classmethod
    def INPUT_TYPES(cls):
        
        prompt_files = init_prompt_files_list()

        return {
            "required": {
                "text": (IO.STRING, {"multiline": True, "dynamicPrompts": True, "tooltip": "The text to be encoded."}),
                "clip": (IO.CLIP, {"tooltip": "The CLIP model used for encoding the text."}),
                "prompt_file": (prompt_files,)
            }
        }
    RETURN_TYPES = (IO.CONDITIONING,IO.CONDITIONING,)
    RETURN_NAMES = ("positive", "negative",)
    OUTPUT_TOOLTIPS = ("A conditioning containing the embedded text used to guide the diffusion model.",)
    FUNCTION = "encode"

    CATEGORY = "ZernaPack/PromptGnerators"
    DESCRIPTION = "Encodes a text prompt using a CLIP model into an embedding that can be used to guide the diffusion model towards generating specific images."

    def encode(self, clip, text, prompt_file):
        if clip is None:
                raise RuntimeError("ERROR: clip input is invalid: None\n\nIf the clip is from a checkpoint loader node your checkpoint does not contain a valid clip or text encoder model.")

        return process_prompts_encode(clip, text, read_file_prompt_data(prompt_file))

class UnzipPrompt:
    @classmethod
    def INPUT_TYPES(s):
        return {"required": {"zipped_prompt": ("ZIPPED_PROMPT",), }}

    RETURN_TYPES = ("STRING", "STRING", "STRING")
    RETURN_NAMES = ("positive", "negative", "name")

    FUNCTION = "doit"

    CATEGORY = "ZernaPack/PromptGnerators"

    def doit(self, zipped_prompt):
        return zipped_prompt
    
class LastImage:
    def __init__(self):
        self.output_dir = folder_paths.get_output_directory()
        self.type = "output"
        self.prefix_append = ""
        self.compress_level = 4

    @classmethod
    def INPUT_TYPES(s):
        return {
            "required": {
                "images": ("IMAGE", {"tooltip": "The images to save."}),
                "filename_prefix": ("STRING", {
                    "default": "ComfyUI",
                    "tooltip": "The prefix for the file to save. This may include formatting information such as %date:yyyy-MM-dd% or %Empty Latent Image.width%."
                })
            },
            "hidden": {
                "prompt": "PROMPT",
                "extra_pnginfo": "EXTRA_PNGINFO"
            },
        }

    RETURN_TYPES = ()
    FUNCTION = "save_images"

    OUTPUT_NODE = True

    CATEGORY = "ZernaPack/PromptGnerators"
    DESCRIPTION = "Saves only the last image from the batch to the ComfyUI output directory."

    def save_images(self, images, filename_prefix="ComfyUI", prompt=None, extra_pnginfo=None):
        filename_prefix += self.prefix_append
        full_output_folder, filename, counter, subfolder, filename_prefix = folder_paths.get_save_image_path(
            filename_prefix, self.output_dir, images[0].shape[1], images[0].shape[0])

        results = []

        # Отримаємо останнє зображення
        last_index = len(images) - 1
        image = images[last_index]

        i = 255. * image.cpu().numpy()
        img = Image.fromarray(np.clip(i, 0, 255).astype(np.uint8))
        metadata = None
        # if not args.disable_metadata:
        #     metadata = PngInfo()
        #     if prompt is not None:
        #         metadata.add_text("prompt", json.dumps(prompt))
        #     if extra_pnginfo is not None:
        #         for x in extra_pnginfo:
        #             metadata.add_text(x, json.dumps(extra_pnginfo[x]))

        filename_with_batch_num = filename.replace("%batch_num%", str(last_index))
        file = f"{filename_with_batch_num}_{counter:05}_.png"
        img.save(os.path.join(full_output_folder, file), pnginfo=metadata, compress_level=self.compress_level)

        results.append({
            "filename": file,
            "subfolder": subfolder,
            "type": self.type
        })

        return { "ui": { "images": results } }



NODE_CLASS_MAPPINGS = {
    "CLIPDynamicPromptEncoder //Zerna Pack": CLIPDynamicPromptEncoder,
    "DynamicPromptInjector //Zerna Pack": DynamicPromptInjector,
    "LastImage //Zerna Pack": LastImage,
    "UnzipPrompt //Zerna Pack": UnzipPrompt
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "CLIPDynamicPromptEncoder //Zerna Pack": "CLIP Dynamic Prompt Encoder (Zerna Pack)",
    "DynamicPromptInjector //Zerna Pack": "Dynamic Prompt Injector (Zerna Pack)",
    "LastImage //Zerna Pack": "Last Image (Zerna Pack)",
    "UnzipPrompt //Zerna Pack": "Unzip Prompt (Zerna Pack)"
}