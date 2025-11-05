import os
import sys
from datetime import datetime

def get_credits() -> str:
    """Generate credits for the CSS file"""
    current_date = datetime.now().strftime("%Y-%m-%d")
    return f"""
/* =========================================
 * WebStyle Framework
 * https://github.com/0kibob/webstyle-framework
 * Built on: {current_date}
 * ========================================= */
"""

def build_style_from_folder(input_path: str, output_path: str) -> None:
    """
    Merge css files from a folder into a single css file.
    - input_path: the path to the folder containing css files
    - output_path: the path to the output folder
    """
    find_files_path: list = []
    sort_files_path: list = []
    priority_order = ["theme.css", "base.css"]

    print(f"Generating CSS from: {input_path}")

    # Look for each valid css file in the input directory and save there path.
    for root, _subfolders, files in os.walk(input_path):
        for file in files:
            if not file.endswith(".css"): continue
            find_files_path.append(os.path.join(root, file))
    
    # Place know file name at the start of the list.
    prioritized_files = [file for file in find_files_path if os.path.basename(file) in priority_order]
    sorted_prioritized_files = sorted(prioritized_files, key=lambda file: priority_order.index(os.path.basename(file)))
    other_files = [file for file in find_files_path if os.path.basename(file) not in priority_order]

    sort_files_path = sorted_prioritized_files + other_files

    # Ensure the output directory exists
    os.makedirs(output_path, exist_ok=True)

    # Write the sorted files to the final file.
    with open(os.path.join(output_path, "webstyle_framework.css"), "w", encoding="utf-8") as outfile:
        for file in sort_files_path:
            outfile.write(f"/* ========== {os.path.basename(file)} ========== */\n")
            with open(file, "r", encoding="utf-8") as f:
                outfile.write(f.read() + "\n\n")
        
        # Add credits at the end of the file
        outfile.write(get_credits())

    print(f"CSS built at: {output_path}")

if __name__ == "__main__":

    if not len(sys.argv) > 1: build_style_from_folder("src/", "build/"); quit()
    if not len(sys.argv) == 3: print("Usage: python build.py <source_folder> <output_folder>"); quit()

    build_style_from_folder(sys.argv[1], sys.argv[2])