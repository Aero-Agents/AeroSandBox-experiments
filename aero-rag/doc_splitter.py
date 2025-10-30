import re
import os
from pathlib import Path
import textwrap


def dedent_content(lines):
    """
    Remove excess indentation from content while preserving relative indentation.
    This ensures that py:class::, py:method::, etc. start at column 0, but
    preserves indentation in lists, nested structures, etc.
    
    The approach:
    1. Find the minimum indentation across ALL non-empty lines
    2. Remove that amount of indentation from all lines
    3. This preserves relative indentation within the content
    
    Args:
        lines: List of lines to dedent
        
    Returns:
        list: Dedented lines
    """
    if not lines:
        return lines
    
    # Find the minimum indentation across all non-empty lines
    min_indent = float('inf')
    
    for line in lines:
        if line.strip():  # Only consider non-empty lines
            indent = len(line) - len(line.lstrip())
            min_indent = min(min_indent, indent)
    
    # If all lines were empty, return as is
    if min_indent == float('inf'):
        return lines
    
    # Remove the minimum indentation from all lines
    dedented_lines = []
    for line in lines:
        if not line.strip():  # Preserve empty lines
            dedented_lines.append('')
        elif len(line) >= min_indent and line[:min_indent].strip() == '':
            # Remove the base indentation
            dedented_lines.append(line[min_indent:])
        else:
            # Line has less indentation than expected, keep as is
            dedented_lines.append(line.lstrip())  # At least strip what we can
    
    return dedented_lines


def extract_class_name(class_line):
    """
    Extract the class name from a py:class:: line.
    Example: ".. py:class:: Opti(variable_categories_to_freeze = None, ...)" -> "Opti"
    Also handles indented nested classes: "   .. py:class:: AeroComponentResults" -> "AeroComponentResults"
    """
    match = re.match(r'\s*\.\.\s+py:class::\s+(\w+)', class_line)
    if match:
        return match.group(1)
    return None


def extract_function_name(function_line):
    """
    Extract the function name from a py:function:: line.
    Example: ".. py:function:: is_casadi_type(object, recursive = True)" -> "is_casadi_type"
    """
    match = re.match(r'\s*\.\.\s+py:function::\s+(\w+)', function_line)
    if match:
        return match.group(1)
    return None


def extract_method_name(method_line):
    """
    Extract the method name from a py:method:: line.
    Example: "   .. py:method:: variable(init_guess = None, ...)" -> "variable"
    """
    match = re.match(r'\s+\.\.\s+py:method::\s+(\w+)', method_line)
    if match:
        return match.group(1)
    return None


def update_method_signature_with_class(method_line, class_name):
    """
    Update a method signature to include the class name.
    Example: "   .. py:method:: area_projected(type = 'XY')" 
             -> "   .. py:method:: Fuselage.area_projected(type = 'XY')"
    
    Args:
        method_line: The original method line
        class_name: The name of the class
        
    Returns:
        str: Updated method line with class name prefix
    """
    match = re.match(r'(\s*\.\.\s+py:method::\s+)(\w+)(\(.*)', method_line)
    if match:
        prefix = match.group(1)
        method_name = match.group(2)
        rest = match.group(3)
        return f"{prefix}{class_name}.{method_name}{rest}"
    return method_line


def has_explanatory_text(lines, start_index):
    """
    Check if an attribute/parameter has explanatory text following it.
    Returns True if there's descriptive text, False if it's just metadata like :value: or :type:
    
    Args:
        lines: List of all lines
        start_index: Index of the attribute/parameter line
        
    Returns:
        bool: True if explanatory text exists
    """
    # Look ahead at the following lines
    base_indent = len(lines[start_index]) - len(lines[start_index].lstrip())
    
    for i in range(start_index + 1, min(start_index + 10, len(lines))):
        line = lines[i]
        
        # If we hit another py directive at the same or lower indentation level, stop
        if line.strip().startswith('.. py:') and len(line) - len(line.lstrip()) <= base_indent:
            break
        
        # Skip empty lines
        if not line.strip():
            continue
            
        # Skip metadata lines (e.g., :value:, :type:)
        if line.strip().startswith(':'):
            continue
        
        # If we find a line with actual text content (not just whitespace or metadata)
        # that's indented more than the base, it's explanatory text
        if line.strip() and len(line) - len(line.lstrip()) > base_indent:
            return True
    
    return False


def should_include_attribute_or_param(lines, index):
    """
    Determine if an attribute or parameter should be included based on whether it has explanatory text.
    
    Args:
        lines: List of all lines
        index: Index of the attribute/parameter line
        
    Returns:
        bool: True if should be included
    """
    line = lines[index]
    
    # Always include if it's not an attribute or parameter
    if not (line.strip().startswith('.. py:attribute::') or line.strip().startswith(':param ')):
        return True
    
    return has_explanatory_text(lines, index)


def should_create_method_file(method_content):
    """
    Determine if a method should have its own .txt file.
    Create a file if:
    - There's content before the :return: line, OR
    - There's a detailed :return: with explanatory text, OR
    - There's no :return: and there's content after the signature
    
    Args:
        method_content: List of lines for the method
        
    Returns:
        bool: True if method file should be created
    """
    if not method_content:
        return False
    
    has_explicit_return = False
    has_detailed_return = False
    content_before_return_count = 0
    content_after_signature_count = 0
    
    for i, line in enumerate(method_content):
        if i == 0:  # Skip the method signature line
            continue
        
        stripped = line.strip()
        
        # Skip empty lines
        if not stripped:
            continue
        
        # Check if this is an explicit :return: line
        if (stripped.startswith(':return:') or
            stripped.startswith(':returns:') or
            stripped.startswith(':yield:') or
            stripped.startswith(':yields:')):
            has_explicit_return = True
            
            # Check if there's text after the :return: on the same line
            return_text_on_same_line = stripped.split(':', 2)[-1].strip() if stripped.count(':') >= 2 else ''
            
            # Look ahead to see if there's explanatory text for the return
            j = i + 1
            return_has_text = len(return_text_on_same_line) > 0
            
            while j < len(method_content):
                next_line = method_content[j]
                next_stripped = next_line.strip()
                
                # Stop if we hit another directive or parameter
                if next_stripped.startswith('.. py:') or next_stripped.startswith(':param') or next_stripped.startswith(':type'):
                    break
                
                # If we find non-empty content, the return is detailed
                if next_stripped:
                    return_has_text = True
                    break
                
                j += 1
            
            has_detailed_return = return_has_text
            # Stop counting content before return
            break
        
        # Skip simple metadata lines
        if stripped.startswith(':'):
            continue
        
        # Count substantial content lines (after signature)
        content_after_signature_count += 1
        
        # If we haven't seen a return yet, count this as content before return
        if not has_explicit_return:
            content_before_return_count += 1
    
    # Create file if there's content before return
    if content_before_return_count > 0:
        return True
    
    # Create file if there's a detailed return
    if has_explicit_return and has_detailed_return:
        return True
    
    # Create file if there's no return but has content
    if not has_explicit_return and content_after_signature_count > 0:
        return True
    
    return False


def split_class_content(lines, class_name):
    """
    Split class content into:
    1. Class overview (everything before the first method, excluding nested classes)
    2. Dictionary of methods with their content
    3. List of nested classes with their content
    
    Only includes attributes/parameters that have explanatory text.
    Method signatures are updated to include the class name (e.g., ClassName.method_name).
    
    Args:
        lines: List of lines for the class
        class_name: Name of the class (used to prefix method signatures)
        
    Returns:
        tuple: (class_overview_lines, methods_dict, nested_classes_list)
    """
    class_overview = []
    methods = {}
    nested_classes = []
    current_method = None
    current_method_content = []
    in_method = False
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Check if this is a nested class definition (not at the start, indented)
        if line.strip().startswith('.. py:class::') and i > 0:
            # This is a nested class - extract it as a separate entity
            nested_class_content = [line]
            nested_class_indent = len(line) - len(line.lstrip())
            i += 1
            
            # Collect all lines belonging to the nested class
            # Lines belong to nested class ONLY if they are MORE indented than the nested class declaration
            # Lines at the SAME indentation as the nested class belong to the parent
            
            while i < len(lines):
                next_line = lines[i]
                next_indent = len(next_line) - len(next_line.lstrip()) if next_line.strip() else 999
                
                # Empty lines belong to current context
                if not next_line.strip():
                    nested_class_content.append(next_line)
                    i += 1
                    continue
                
                # If this line is at same or less indentation than nested class declaration, it belongs to parent
                if next_indent <= nested_class_indent:
                    break
                
                # Otherwise, content is more indented than nested class, so it belongs to nested class
                nested_class_content.append(next_line)
                i += 1
            
            nested_classes.append(nested_class_content)
            continue
        
        # Check if this is an attribute/parameter without explanatory text - skip it
        if (line.strip().startswith('.. py:attribute::') or line.strip().startswith(':param ')) and not line.startswith('      '):
            if not should_include_attribute_or_param(lines, i):
                # Skip this attribute and its metadata lines
                base_indent = len(line) - len(line.lstrip())
                i += 1
                # Skip following metadata lines
                while i < len(lines):
                    next_line = lines[i]
                    if next_line.strip().startswith('.. py:') and len(next_line) - len(next_line.lstrip()) <= base_indent:
                        break
                    if not next_line.strip() or next_line.strip().startswith(':'):
                        i += 1
                    else:
                        # We've hit content, which means we were wrong - this shouldn't happen
                        # due to has_explanatory_text check, but just in case
                        break
                continue
        
        # Check if this is a method definition (not nested inside another structure)
        if line.strip().startswith('.. py:method::') and not line.startswith('      '):
            # Save previous method if exists
            if current_method and current_method_content:
                methods[current_method] = current_method_content
            
            # Start new method
            method_name = extract_method_name(line)
            if method_name:
                current_method = method_name
                # Update method signature with class name for method content
                updated_method_line = update_method_signature_with_class(line, class_name)
                current_method_content = [updated_method_line]
                in_method = True
                
                # Add updated method signature to overview
                class_overview.append(updated_method_line)
        elif in_method:
            # Check if we're starting a new top-level method or attribute (not nested)
            if ((line.strip().startswith('.. py:method::') and not line.startswith('      ')) or 
                (line.strip().startswith('.. py:attribute::') and not line.startswith('      ')) or
                (line.startswith('.. py:class::')) or
                (line.startswith('.. py:') and not line.startswith('   '))):
                # We've hit the next element, save current method
                if current_method and current_method_content:
                    methods[current_method] = current_method_content
                
                # Reset method tracking
                in_method = False
                current_method = None
                current_method_content = []
                
                # Check if this attribute should be included
                if line.strip().startswith('.. py:attribute::'):
                    if should_include_attribute_or_param(lines, i):
                        class_overview.append(line)
                    # If not included, skip it (it won't be added to overview)
                else:
                    # This line is part of class overview
                    class_overview.append(line)
            else:
                # Add to current method content
                current_method_content.append(line)
        else:
            # Part of class overview
            class_overview.append(line)
        
        i += 1
    
    # Save last method if exists
    if current_method and current_method_content:
        methods[current_method] = current_method_content
    
    return class_overview, methods, nested_classes


def split_docs_into_classes(input_file, output_dir):
    """
    Split the full_docs.txt file into structured class and function documentation.
    
    For each class:
    - Creates a folder named after the class
    - Creates a main class file with overview, attributes, and method signatures
    - Creates a methods/ subfolder with individual method files
    - Nested classes are saved as separate top-level folders with parent.NestedClass naming
    
    For each function:
    - Creates a folder named after the function
    - Creates a .txt file with the function documentation
    
    Args:
        input_file: Path to the full_docs.txt file
        output_dir: Directory where class and function folders will be created
    """
    # Create output directory if it doesn't exist
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Read the entire file
    with open(input_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split by lines to find class and function boundaries
    lines = content.split('\n')
    
    # Track current class/function and its content
    current_class = None
    current_function = None
    current_content = []
    class_count = 0
    function_count = 0
    method_count = 0
    nested_class_count = 0
    
    # Keep track of seen classes to handle duplicates
    seen_classes = {}
    seen_functions = {}
    
    for i, line in enumerate(lines):
        # Check if this is a new class definition
        if line.startswith('.. py:class::'):
            # Save previous class or function if exists
            if current_class and current_content:
                counts = save_class_documentation(
                    current_class, current_content, output_path, 
                    seen_classes, class_count, method_count, nested_class_count
                )
                class_count, method_count, nested_class_count = counts
            elif current_function and current_content:
                function_count = save_function_documentation(
                    current_function, current_content, output_path,
                    seen_functions, function_count
                )
            
            # Start new class
            class_name = extract_class_name(line)
            if class_name:
                current_class = class_name
                current_function = None
                current_content = [line]
            else:
                print(f"Warning: Could not extract class name from line {i+1}: {line}")
                current_content = [line]
        # Check if this is a new function definition
        elif line.startswith('.. py:function::'):
            # Save previous class or function if exists
            if current_class and current_content:
                counts = save_class_documentation(
                    current_class, current_content, output_path, 
                    seen_classes, class_count, method_count, nested_class_count
                )
                class_count, method_count, nested_class_count = counts
            elif current_function and current_content:
                function_count = save_function_documentation(
                    current_function, current_content, output_path,
                    seen_functions, function_count
                )
            
            # Start new function
            function_name = extract_function_name(line)
            if function_name:
                current_function = function_name
                current_class = None
                current_content = [line]
            else:
                print(f"Warning: Could not extract function name from line {i+1}: {line}")
                current_content = [line]
        else:
            # Add line to current class or function content
            if current_class or current_function or current_content:
                current_content.append(line)
    
    # Save the last class or function
    if current_class and current_content:
        counts = save_class_documentation(
            current_class, current_content, output_path,
            seen_classes, class_count, method_count, nested_class_count
        )
        class_count, method_count, nested_class_count = counts
    elif current_function and current_content:
        function_count = save_function_documentation(
            current_function, current_content, output_path,
            seen_functions, function_count
        )
    
    print(f"\nTotal classes saved: {class_count}")
    print(f"Total nested classes saved: {nested_class_count}")
    print(f"Total methods saved: {method_count}")
    print(f"Total functions saved: {function_count}")
    print(f"Output directory: {output_path.absolute()}")


def save_class_documentation(class_name, content_lines, output_path, seen_classes, class_count, method_count, nested_class_count):
    """
    Save class documentation with separate files for methods and nested classes.
    All files are saved at the same level in class_docs directory with naming:
    - ClassName.txt for class overview
    - ClassName.method_name.txt for methods
    - ClassName.NestedClass.txt for nested classes
    
    Duplicate classes are ignored (only the first occurrence is saved).
    
    Returns:
        tuple: (updated_class_count, updated_method_count, updated_nested_class_count)
    """
    # Skip duplicate class names
    if class_name in seen_classes:
        print(f"Skipping duplicate class: {class_name}")
        return class_count, method_count, nested_class_count
    else:
        seen_classes[class_name] = True
        base_name = class_name
    
    # Split content into overview, methods, and nested classes
    # Use the original class_name (not base_name) for method signatures
    class_overview, methods, nested_classes = split_class_content(content_lines, class_name)
    
    # Save class overview at the top level
    class_file = output_path / f"{base_name}.txt"
    with open(class_file, 'w', encoding='utf-8') as f:
        dedented_overview = dedent_content(class_overview)
        f.write('\n'.join(dedented_overview))
    
    nested_count = len(nested_classes)
    print(f"Saved class: {base_name}.txt ({len(methods)} methods, {nested_count} nested classes)")
    
    # Save methods at the top level with ClassName.method_name.txt naming
    if methods:
        for method_name, method_content in methods.items():
            # Check if method has substantial content beyond signature and return line
            if should_create_method_file(method_content):
                method_file = output_path / f"{base_name}.{method_name}.txt"
                with open(method_file, 'w', encoding='utf-8') as f:
                    dedented_method = dedent_content(method_content)
                    f.write('\n'.join(dedented_method))
                method_count += 1
    
    # Save nested classes as ClassName.NestedClass.txt files at the top level
    if nested_classes:
        for nested_class_content in nested_classes:
            # Extract the nested class name
            nested_class_name = None
            if nested_class_content:
                nested_class_name = extract_class_name(nested_class_content[0])
            
            if nested_class_name:
                # Filter nested class content to remove attributes without explanatory text
                filtered_nested_content = filter_nested_class_content(nested_class_content)
                
                # Save as ClassName.NestedClass.txt at the top level
                nested_file = output_path / f"{base_name}.{nested_class_name}.txt"
                with open(nested_file, 'w', encoding='utf-8') as f:
                    dedented_nested = dedent_content(filtered_nested_content)
                    f.write('\n'.join(dedented_nested))
                nested_class_count += 1
    
    class_count += 1
    return class_count, method_count, nested_class_count


def save_function_documentation(function_name, content_lines, output_path, seen_functions, function_count):
    """
    Save function documentation as a single .txt file at the top level.
    
    Duplicate functions are ignored (only the first occurrence is saved).
    
    Returns:
        int: updated function_count
    """
    # Skip duplicate function names
    if function_name in seen_functions:
        print(f"Skipping duplicate function: {function_name}")
        return function_count
    else:
        seen_functions[function_name] = True
        base_name = function_name
    
    # Save function documentation as a single .txt file at the top level
    function_file = output_path / f"{base_name}.txt"
    with open(function_file, 'w', encoding='utf-8') as f:
        dedented_content = dedent_content(content_lines)
        f.write('\n'.join(dedented_content))
    
    print(f"Saved function: {base_name}.txt")
    
    function_count += 1
    return function_count


def filter_nested_class_content(content_lines):
    """
    Filter nested class content to remove attributes/parameters without explanatory text.
    
    Args:
        content_lines: List of lines for the nested class
        
    Returns:
        list: Filtered lines
    """
    filtered = []
    i = 0
    
    while i < len(content_lines):
        line = content_lines[i]
        
        # Check if this is an attribute/property/parameter without explanatory text
        if (line.strip().startswith('.. py:attribute::') or 
            line.strip().startswith('.. py:property::') or
            line.strip().startswith(':param ')):
            
            if should_include_attribute_or_param(content_lines, i):
                # Include this and continue normally
                filtered.append(line)
            else:
                # Skip this attribute and its metadata
                base_indent = len(line) - len(line.lstrip())
                i += 1
                # Skip following metadata and empty lines
                while i < len(content_lines):
                    next_line = content_lines[i]
                    next_indent = len(next_line) - len(next_line.lstrip()) if next_line.strip() else 999
                    
                    # Stop if we hit a py directive at same or lesser indentation
                    if next_line.strip().startswith('.. py:') and next_indent <= base_indent:
                        break
                    
                    # Skip metadata lines and empty lines
                    if not next_line.strip() or next_line.strip().startswith(':'):
                        i += 1
                    else:
                        # We found content, which means it should have been included
                        # This shouldn't happen if should_include_attribute_or_param works correctly
                        break
                continue
        else:
            filtered.append(line)
        
        i += 1
    
    return filtered


def save_nested_class_as_top_level(nested_class_name, content_lines, output_path, class_count, method_count):
    """
    DEPRECATED: Nested classes are now saved as single .txt files in parent folder.
    This function is kept for backward compatibility but should not be used.
    """
    pass


if __name__ == "__main__":
    # Define paths
    script_dir = Path(__file__).parent
    input_file = script_dir / "full_docs.txt"
    output_dir = script_dir / "clean_docs"
    
    # Check if input file exists
    if not input_file.exists():
        print(f"Error: Input file not found: {input_file}")
        exit(1)
    
    print(f"Reading from: {input_file}")
    print(f"Saving to: {output_dir}")
    print("-" * 60)
    
    # Split the documentation
    split_docs_into_classes(input_file, output_dir)
