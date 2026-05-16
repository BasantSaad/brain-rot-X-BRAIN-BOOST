import os
import ast

# ----------------------------
# STORAGE
# ----------------------------
classes_data = {}
relationships = []

# List of common builtins to ignore for clean UML relationships
BUILTIN_IGNORE = {
    "print", "len", "int", "str", "float", "dict", "list", "set", "tuple", 
    "super", "init", "range", "enumerate", "isinstance", "append", "any", "all"
}

# ----------------------------
# COMPONENT PARSERS
# ----------------------------
def extract_type_name(node):
    """Safely extracts type names from annotations, handling strings, 
    Name nodes, and Generic types like List[UserProfile]."""
    if isinstance(node, ast.Name):
        return node.id
    elif isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    elif isinstance(node, ast.Subscript): # Handles List[Model] or Dict[str, Model]
        return extract_type_name(node.slice)
    elif isinstance(node, ast.Tuple):
        types = [extract_type_name(e) for e in node.elts]
        return [t for t in types if t]
    return None

# ----------------------------
# CLASS ANALYSIS
# ----------------------------
def analyze_class(node):
    class_info = {
        "name": node.name,
        "bases": [],
        "attributes": [],
        "methods": []
    }

    # 1. INHERITANCE
    for base in node.bases:
        if isinstance(base, ast.Name):
            class_info["bases"].append(base.id)
            relationships.append((node.name, base.id, "INHERITS"))
        elif isinstance(base, ast.Attribute): # Handles package.BaseClass
            class_info["bases"].append(base.attr)
            relationships.append((node.name, base.attr, "INHERITS"))

    # 2. CLASS BODY SCAN
    for item in node.body:

        # METHODS
        if isinstance(item, ast.FunctionDef):
            class_info["methods"].append(item.name)

            # Look inside the method body
            for sub in ast.walk(item):
                # INSTANCE ATTRIBUTES (self.x = value)
                if isinstance(sub, ast.Assign):
                    for t in sub.targets:
                        if (isinstance(t, ast.Attribute) 
                                and isinstance(t.value, ast.Name) 
                                and t.value.id == "self"):
                            class_info["attributes"].append(t.attr)

                # DEPENDENCY (Method calls / Class instantiations)
                elif isinstance(sub, ast.Call):
                    if isinstance(sub.func, ast.Name):
                        called_name = sub.func.id
                        if called_name not in BUILTIN_IGNORE and called_name != node.name:
                            relationships.append((node.name, called_name, "USES"))

        # DATACLASS FIELDS & TYPED ATTRIBUTES (name: Type)
        elif isinstance(item, ast.AnnAssign):
            if isinstance(item.target, ast.Name):
                attr_name = item.target.id
                class_info["attributes"].append(attr_name)
                
                # Extract dependency from the type annotation definition
                type_name = extract_type_name(item.annotation)
                if type_name and type_name not in BUILTIN_IGNORE:
                    if isinstance(type_name, list):
                        for t in type_name:
                            relationships.append((node.name, t, "USES"))
                    else:
                        relationships.append((node.name, type_name, "USES"))

        # CLASS VARIABLES (Handle tuples and single assignments safely)
        elif isinstance(item, ast.Assign):
            for target in item.targets:
                if isinstance(target, ast.Name):
                    class_info["attributes"].append(target.id)
                elif isinstance(target, (ast.Tuple, ast.List)):
                    for elt in target.elts:
                        if isinstance(elt, ast.Name):
                            class_info["attributes"].append(elt.id)

    # Clean up duplicate entries cleanly
    class_info["attributes"] = list(sorted(set(class_info["attributes"])))
    return class_info

# ----------------------------
# FILE PARSER
# ----------------------------
def extract_from_file(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        try:
            tree = ast.parse(f.read(), filename=path)
        except SyntaxError:
            return []

    classes = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            classes.append(analyze_class(node))
    return classes

# ----------------------------
# PROJECT SCANNER
# ----------------------------
def scan_project(root="."):
    result = {}
    for r, _, files in os.walk(root):
        for f in files:
            if f.endswith(".py"):
                path = os.path.join(r, f)
                try:
                    classes = extract_from_file(path)
                    if classes:
                        result[path] = classes
                except Exception as e:
                    print(f"Error reading file {path}: {e}")
    return result

# ----------------------------
# RUN EXECUTION & OUTPUT CLEANING
# ----------------------------
data = scan_project()
all_found_classes = set()

for file, classes in data.items():
    for c in classes:
        classes_data[c["name"]] = c
        all_found_classes.add(c["name"])

# Output filtered structural relationships
print("\n========================")
print("STRUCTURAL RELATIONSHIPS")
print("========================\n")

unique_rel = list(set(relationships))
for source, target, rel_type in unique_rel:
    # Only show relationships if the target is an internal project class
    if target in all_found_classes:
        print(f"{source} --[{rel_type}]--> {target}")