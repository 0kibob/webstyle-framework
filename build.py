import os
import sys
import json
import re

class Project:

    def __init__(self, path: str, config: dict):
        self.path: str = path
        self.config: dict = config
        self.name: str = config["name"].lower()
        self.author: str = config["author"]


def read_json(path: str) -> dict:
    # simply read the json file to a python dict
    with open(path, "r", encoding="utf-8") as f: return json.load(f)


def find_project_at(path: str) -> list[Project]:

    # Look for all subfolder of the input path
    project_folders: list = [[folder.name, folder.path] for folder in os.scandir(path) if folder.is_dir()]
    print(f'INFO  | Found {len(project_folders)} folder(s) at "{path}"')
    
    valid_projects: list[Project] = []

    for project in project_folders:

        # Check for project validity
        project_config_path: str = os.path.join(project[1], f"{project[0]}.json")
        if not os.path.isfile(project_config_path): 
            print(f'ERROR | {project[0]} at "{project[1]}" is not a valid project folder or missing {project[0]}.json'); continue
        print(f'INFO  | {project[0]} at "{project[1]}" detect as a valid project folder')
        
        # Get the project config as dict
        project_config: dict = read_json(project_config_path)
        project: Project = Project(project[1], project_config)
        
        valid_projects.append(project)

    return valid_projects












def make_project_credit(name: str, author: str) -> str:
    return f"""/*
 | {name}, by {author}
 | Build using WebStyle Framework
 | Copyright (c) 2025 LAURET Timéo
 | https://github.com/0kibob/webstyle-framework
*/
"""

def make_project_root(roots: dict[str, str]) -> str:
    lines = [":root\n{"]
    lines.extend(f"    {var}: {value};" for var, value in roots.items())
    lines.append("}")
    return "\n".join(lines)


def get_project_subfiles_path(path: str, order: list | None) -> list[str]:
    
    valid_file: list[str] = []
    ordered_file: list[str] = []
    # Look over all the file in the project folder
    for root, _subfolders, files in os.walk(path):
        valid_file = [os.path.join(root, f) for f in files if f.endswith(".css")]

    if not order: return valid_file
    order_map = {name: i for i, name in enumerate(order)}
    ordered_file = sorted(valid_file, key=lambda f: (order_map.get(os.path.basename(f), float("inf"))))
    return ordered_file

def get_project_subfiles_root(subfiles: list[str]) -> dict[str, str]:

    subfile_root: dict[str, str] = {}

    for subfile in subfiles:
        with open(subfile, "r", encoding="utf-8") as f: content = f.read()
        content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
        subfile_root.update({
            key.strip(): value.strip()
            for root in re.findall(r":root\s*{([^}]*)}", content, re.DOTALL)
            for key, value in re.findall(r"([^:;]+)\s*:\s*([^;]+)", root)
        })

    return subfile_root

def get_project_subfiles_contents(subfiles: list[str]) -> list[str]:

    subfiles_content: list[str] = []

    for subfile in subfiles:
        with open(subfile, "r", encoding="utf-8") as f: content = f.read()
        content = re.sub(r":root\s*{[^}]*}", "", content, flags=re.DOTALL)
        if content: subfiles_content.append(content.strip())
        subfiles_content.append("")

    return subfiles_content


def get_project_generator(generator_name: str, generator: dict, project_root: dict) -> list[str]:

    generator_content: list[str] = []

    generator_prefix: str = generator.get("prefix")
    generator_val_key: str = generator.get("val-key")
    generator_css_key: str = generator.get("css-key")
    generator_step: int = generator.get("step")
    # Special
    generator_auto: bool = generator.get("auto")
    generator_scales: dict = generator.get("scales", {})
    generator_directions: list[dict] = generator.get("directions", [])

    if generator_val_key.startswith('--') and generator_val_key not in project_root: generator_val_key = None
    if not generator_prefix: 
        generator_content.append(f'/* ERROR | Generator "{generator_name}" references undefined for "prefix" */')
        print(f'ERROR | Generator "{generator_name}" references undefined for "prefix"'); return generator_content
    if not generator_val_key:
        generator_content.append(f'/* ERROR | Generator "{generator_name}" references undefined for "val-key" */')
        print(f'ERROR | Generator "{generator_name}" references undefined for "val-key"'); return generator_content
    if not generator_css_key:
        generator_content.append(f'/* ERROR | Generator "{generator_name}" references undefined for "css-key" */')
        print(f'ERROR | Generator "{generator_name}" references undefined for "css-key"'); return generator_content
    if not generator_step:
        generator_content.append(f'/* ERROR | Generator "{generator_name}" references undefined for "step" */')
        print(f'ERROR | Generator "{generator_name}" references undefined for "step"'); return generator_content

    if generator_auto: generator_content.append( f".{generator_prefix}-auto {{ {generator_css_key}: auto; }}" )

    value = f"var({generator_val_key})" if generator_val_key.startswith('--') else generator_val_key

    for scale_name, scale_value in generator_scales.items():
        generator_content.append(f".{generator_prefix}-{scale_name} {{ {generator_css_key}: calc({value} * {scale_value}); }}")

    for i in range(generator_step + 1):
        generator_content.append(f".{generator_prefix}-{i} {{ {generator_css_key}: calc({value} * {i}); }}")
    
    if not generator_directions: return generator_content

    for direction in generator_directions:
        prefix = direction.get("prefix")
        css_subkey = direction.get("css-subkey")

        if generator_auto: generator_content.append( f".{prefix}-auto {{ {generator_css_key}-{css_subkey}: auto; }}" )

        for scale_name, scale_value in generator_scales.items():
            generator_content.append(f".{prefix}-{scale_name} {{ {generator_css_key}-{css_subkey}: calc({value} * {scale_value}); }}")

        for i in range(generator_step + 1):
            generator_content.append(f".{prefix}-{i} {{ {generator_css_key}-{css_subkey}: calc({value} * {i}); }}")

    return generator_content


def build_project(project: Project, out_path: str):

    print(f'INFO  | Building project {project.name}')

    config_roots: dict = project.config.get("roots")
    config_generators: dict = project.config.get("generators")
    config_colors: dict = project.config.get("colors")
    config_order: list = project.config.get("files_priority_order")
    
    project_root: dict[str, str] = {}
    project_subfiles: list[str] = []
    project_generator: list[str] = []
    project_content: list[str] = []

    project_subfiles = get_project_subfiles_path(project.path, config_order)

    # Create the project :root css
    if config_roots: project_root.update(config_roots)
    if config_colors: project_root.update(config_colors)
    project_root.update(get_project_subfiles_root(project_subfiles))

    project_content.extend(get_project_subfiles_contents(project_subfiles))

    for i, generator in config_generators.items():
        generator_content: list[str] = get_project_generator(i, generator, project_root)
        if not generator_content: continue
        project_generator.append("")
        project_generator.extend(generator_content)

    with open(os.path.join(out_path, f"{project.name}.webstyle_framework.css"), "w", encoding="utf-8") as outfile:
        outfile.write(make_project_credit(project.name, project.author) + "\n")
        outfile.write(make_project_root(project_root) + "\n")
        outfile.write("\n".join(project_generator) + "\n")
        outfile.write("\n".join(project_content))
    
    print(f'INFO  | Success building project {project.name}')


def build_projects(projects: list[Project], out_path: str):
    
    os.makedirs(out_path, exist_ok=True)
    for project in projects: build_project(project, out_path)


if __name__ == "__main__":

    if not len(sys.argv) > 1: build_projects(find_project_at("src/"), "build/"); quit()
    if not len(sys.argv) == 3: print("Usage: python build.py <source_folder> <output_folder>"); quit()
    build_projects(find_project_at(sys.argv[1]), sys.argv[2])
