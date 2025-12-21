import os
import sys
import json
import re

class Project:

    def __init__(self, path: str, config: dict):
        self.path: str = path
        self.config: dict = config


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




def create_project_credit(name: str, author: str) -> str:
    return f"""/*
 | {name}, by {author}
 | Build using WebStyle Framework
 | Copyright (c) 2025 LAURET Timéo
 | https://github.com/0kibob/webstyle-framework
*/
"""

def create_project_root(roots: dict[str, str]) -> str:
    lines = [":root\n{"]
    lines.extend(f"    {var}: {value};" for var, value in roots.items())
    lines.append("}")
    return "\n".join(lines)

def get_project_subfiles(path: str, order: list | None) -> list[str]:
    
    valid_file: list[str] = []
    ordered_file: list[str] = []

    for root, _subfolders, files in os.walk(path):
        valid_file = [os.path.join(root, f) for f in files if f.endswith(".css")]

    if not order: return valid_file
    order_map = {name: i for i, name in enumerate(order)}
    ordered_file = sorted(valid_file, key=lambda f: (order_map.get(os.path.basename(f), float("inf"))))
    return ordered_file

def get_subfiles_root(subfiles: list[str]) -> dict[str, str]:

    root: dict[str, str] = {}

    for subfile in subfiles:
        with open(subfile, "r", encoding="utf-8") as f: content = f.read()
        content = re.sub(r"/\*.*?\*/", "", content, flags=re.DOTALL)
        root.update({
            key.strip(): value.strip()
            for root in re.findall(r":root\s*{([^}]*)}", content, re.DOTALL)
            for key, value in re.findall(r"([^:;]+)\s*:\s*([^;]+)", root)
        })

    return root

def get_subfiles_content(subfiles: list[str]) -> str:
    
    f_content: list[str] = []

    for subfile in subfiles:
        with open(subfile, "r", encoding="utf-8") as f: content = f.read()
        content = re.sub(r":root\s*{[^}]*}", "", content, flags=re.DOTALL)
        if content:
            f_content.append(content.strip())
            f_content.append("")

    return "\n".join(f_content)




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



def base_generator(generator: dict, project_root: dict, project_settings: dict) -> list[str]:

    generated_css: list[str] = []

    generator_prefix: str = generator.get("prefix")
    generator_val_key: str = generator.get("val-key")
    generator_css_key: str = generator.get("css-key")
    generator_as_auto: bool = generator.get("as-auto")
    generator_as_scale: bool = generator.get("as-scale")
    generator_varient: list[dict] = generator.get("variants")
    generator_step: int = generator.get("step")
    generator_scales: dict = generator.get("scales")

    step = generator_step if generator_step else project_settings.get("step")

    if not generator_prefix: return generated_css
    if not generator_val_key: return generated_css
    if not generator_css_key: return generated_css
    if not step: return generated_css

    if generator_as_auto: generated_css.append( f".{generator_prefix}-auto {{ {generator_css_key}: auto; }}" )
    value = f"var({generator_val_key})" if generator_val_key.startswith('--') else generator_val_key

    if generator_as_scale:
        scales = generator_scales if generator_scales else project_settings.get("scales")
        for scale_name, scale_value in scales.items():
            generated_css.append(f".{generator_prefix}-{scale_name} {{ {generator_css_key}: calc({value} * {scale_value}); }}")

    for i in range(step + 1):
        generated_css.append(f".{generator_prefix}-{i} {{ {generator_css_key}: calc({value} * {i}); }}")
    
    if not generator_varient: return generated_css

    for direction in generator_varient:
        prefix = direction.get("prefix")
        css_subkey = direction.get("css-subkey")

        if generator_as_auto: generated_css.append( f".{prefix}-auto {{ {generator_css_key}-{css_subkey}: auto; }}" )

        if generator_as_scale:
            scales = generator_scales if generator_scales else project_settings.get("scales")
            for scale_name, scale_value in scales.items():
                generated_css.append(f".{prefix}-{scale_name} {{ {generator_css_key}-{css_subkey}: calc({value} * {scale_value}); }}")

        for i in range(step + 1):
            generated_css.append(f".{prefix}-{i} {{ {generator_css_key}-{css_subkey}: calc({value} * {i}); }}")

    return generated_css

def color_generator(generator: dict, colors: dict) -> list[str]:
    
    generated_css: list[str] = []

    generator_prefix: str = generator.get("prefix")
    generator_css_key: str = generator.get("css-key")
    generator_is_hover: bool = generator.get("is-hover")

    if not generator_prefix: return generated_css
    if not generator_css_key: return generated_css

    is_hover: str = ":hover" if generator_is_hover else ""

    generated_css.append(f".{generator_prefix}-none{is_hover} {{ {generator_css_key}: transparent; }}")
    for color_key in colors:
        color = color_key.lstrip("-")
        generated_css.append(f".{generator_prefix}-{color}{is_hover} {{ {generator_css_key}: var({color_key}); }}")

    return generated_css


def build_project(project: Project, out_path: str) -> None:

    project_name: str = project.config.get("name")          # Should give an error if missing
    project_author: str = project.config.get("author")      # Should give an error if missing

    if not project_name: return
    if not project_author: return

    project_settings: dict = project.config.get("setting")
    project_roots: dict = project.config.get("roots")
    project_colors: dict = project.config.get("colors")
    project_colors_generators: list[dict] = project.config.get("colors-generators")
    project_generators: list[dict] = project.config.get("generators")
    project_priority_order: dict = project.config.get("priority-order")
    project_subfiles: list[str] = get_project_subfiles(project.path, project_priority_order)

    generated_roots: str = ""
    generated_colors: str = ""
    generated_generators: str = ""
    generated_content: str = ""
    
    temporary_root: dict[str, str] = {}
    temporary_root.update(project_roots)
    temporary_root.update(project_colors)
    temporary_root.update(get_subfiles_root(project_subfiles))
    generated_roots = create_project_root(temporary_root)
    
    generated_content = get_subfiles_content(project_subfiles)

    if project_colors_generators and project_colors:
        temporary_colors: list[str] = []
        for generator in project_colors_generators:
            css = color_generator(generator, project_colors)
            if css: temporary_colors.extend(css)
            if css: temporary_colors.append("")

        generated_colors = "\n".join(temporary_colors)

    if project_generators:
        temporary_generators: list[str] = []
        for generator in project_generators:
            css = base_generator(generator, project_roots, project_settings)
            if css: temporary_generators.extend(css)
            if css: temporary_generators.append("")

        generated_generators = "\n".join(temporary_generators)

    with open(os.path.join(out_path, f"{project_name.lower()}.webstyle_framework.css"), "w", encoding="utf-8") as outfile:
        outfile.write(create_project_credit(project_name, project_author) + "\n")
        outfile.write(generated_roots + "\n\n")
        outfile.write(generated_colors + "\n")
        outfile.write(generated_generators + "\n")
        outfile.write(generated_content)


def build_projects(projects: list[Project], out_path: str):
    
    os.makedirs(out_path, exist_ok=True)
    for project in projects: build_project(project, out_path)


if __name__ == "__main__":

    if not len(sys.argv) > 1: build_projects(find_project_at("src/"), "build/"); quit()
    if not len(sys.argv) == 3: print("Usage: python build.py <source_folder> <output_folder>"); quit()
    build_projects(find_project_at(sys.argv[1]), sys.argv[2])
