import os
import sys

def credits_for(name: str, author: str) -> str:
    return f"""/*
 ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 ┃ {name}, by {author}
 ┃ Build using WebStyle Framework
 ┃ Copyright (c) 2025 LAURET Timéo
 ┃ https://github.com/0kibob/webstyle-framework
 ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
*/
"""


def read_info_file(file_path: str) -> dict:
    
    data: dict = {}
    
    with open(file_path, "r") as f:
        for line in f:
            if "#" in line: break
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip().strip('"')
                data[key] = value
    
    return data


def get_folders(input_path: str) -> dict:

    folders: list = [[f.name, f.path] for f in os.scandir(input_path) if f.is_dir()]
    valid_folders: dict = {}

    for folder in folders:
        info_path: str = os.path.join(folder[1], f"{folder[0]}.info")
        if os.path.isfile(info_path): valid_folders[folder[0]] = [folder[1], read_info_file(info_path)]
        else: pass

    return valid_folders


def build_folders(folder_dict: dict, output_path: str):
    
    os.makedirs(output_path, exist_ok=True)

    for folder, content in folder_dict.items():
        folder_path: str = content[0]
        folder_info: dict = content[1]

        find_files_path: list = []
        sort_files_path: list = []
        priority_order = folder_info["priority_order"]

        for root, _subfolders, files in os.walk(folder_path):
            for f in files:
                if not f.endswith(".css"): continue
                find_files_path.append(os.path.join(root, f))
        
        prioritized_files = [file for file in find_files_path if os.path.basename(file) in priority_order]
        sorted_prioritized_files = sorted(prioritized_files, key=lambda file: priority_order.index(os.path.basename(file)))
        other_files = [file for file in find_files_path if os.path.basename(file) not in priority_order]
        sort_files_path = sorted_prioritized_files + other_files

        with open(os.path.join(output_path, f"{folder_info["name"].lower()}.webstyle_framework.css"), "w", encoding="utf-8") as outfile:
            outfile.write(credits_for(folder_info["name"], folder_info["author"]) + "\n")
            for f in sort_files_path:
                with open(f, "r", encoding="utf-8") as wf: outfile.write(wf.read() + "\n\n")


if __name__ == "__main__":

    if not len(sys.argv) > 1: build_folders(get_folders("src/"), "build/"); quit()
    if not len(sys.argv) == 3: print("Usage: python build.py <source_folder> <output_folder>"); quit()
    build_folders(get_folders(sys.argv[1]), sys.argv[2])
