import os
import re

def show_current_patterns():
    """Show the current patterns that need to be changed"""
    print("CURRENT PATTERNS TO BE REPLACED:")
    print("=" * 50)
    
    # 1. runtime.py - _RE_PROC_CALL
    print("\n1. mini_basic/runtime.py - _RE_PROC_CALL:")
    try:
        with open('mini_basic/runtime.py', 'r') as f:
            lines = f.readlines()
            for i, line in enumerate(lines[120:130], 121):  # Around line 123
                if '_RE_PROC_CALL' in line:
                    print(f"   Line {i}: {line.rstrip()}")
                    # Show the actual regex pattern
                    if 're.compile(' in line:
                        # Get the full pattern (might span multiple lines)
                        pattern_lines = []
                        j = i-1
                        while j < len(lines) and ('re.compile(' in lines[j] or ')' not in lines[j] or not lines[j].strip().endswith(')')):
                            pattern_lines.append(lines[j].rstrip())
                            j += 1
                        if j < len(lines):
                            pattern_lines.append(lines[j].rstrip())
                        print(f"   Full pattern: {''.join(pattern_lines)}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # 2. runtime.py - _RE_DEF_PROC
    print("\n2. mini_basic/runtime.py - _RE_DEF_PROC:")
    try:
        with open('mini_basic/runtime.py', 'r') as f:
            lines = f.readlines()
            for i, line in enumerate(lines[124:134], 125):  # Around line 127
                if '_RE_DEF_PROC' in line:
                    print(f"   Line {i}: {line.rstrip()}")
                    # Show the actual regex pattern
                    if 're.compile(' in line:
                        # Get the full pattern (might span multiple lines)
                        pattern_lines = []
                        j = i-1
                        while j < len(lines) and ('re.compile(' in lines[j] or ')' not in lines[j] or not lines[j].strip().endswith(')')):
                            pattern_lines.append(lines[j].rstrip())
                            j += 1
                        if j < len(lines):
                            pattern_lines.append(lines[j].rstrip())
                        print(f"   Full pattern: {''.join(pattern_lines)}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # 3. expr/patterns.py - RE_FN_CALL
    print("\n3. mini_basic/expr/patterns.py - RE_FN_CALL:")
    try:
        with open('mini_basic/expr/patterns.py', 'r') as f:
            lines = f.readlines()
            for i, line in enumerate(lines[54:64], 55):  # Around line 57
                if 'RE_FN_CALL' in line:
                    print(f"   Line {i}: {line.rstrip()}")
                    # Show the actual regex pattern
                    if 're.compile(' in line:
                        # Get the full pattern (might span multiple lines)
                        pattern_lines = []
                        j = i-1
                        while j < len(lines) and ('re.compile(' in lines[j] or ')' not in lines[j] or not lines[j].strip().endswith(')')):
                            pattern_lines.append(lines[j].rstrip())
                            j += 1
                        if j < len(lines):
                            pattern_lines.append(lines[j].rstrip())
                        print(f"   Full pattern: {''.join(pattern_lines)}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # 4. runtime_parts/defs.py - Three instances of self._VAR_BASE_PATTERN
    print("\n4. mini_basic/runtime_parts/defs.py - self._VAR_BASE_PATTERN:")
    try:
        with open('mini_basic/runtime_parts/defs.py', 'r') as f:
            lines = f.readlines()
            matches = []
            for i, line in enumerate(lines):
                if 'self._VAR_BASE_PATTERN' in line:
                    matches.append((i+1, line.rstrip()))
            for line_num, line_content in matches:
                print(f"   Line {line_num}: {line_content}")
    except Exception as e:
        print(f"   Error: {e}")
    
    # 5. runtime_parts/program.py - _parse_proc_call pattern
    print("\n5. mini_basic/runtime_parts/program.py - _parse_proc_call pattern:")
    try:
        with open('mini_basic/runtime_parts/program.py', 'r') as f:
            lines = f.readlines()
            for i, line in enumerate(lines[1150:1160], 1151):  # Around line 1154
                if '_VAR_BASE_PATTERN' in line:
                    print(f"   Line {i}: {line.rstrip()}")
    except Exception as e:
        print(f"   Error: {e}")

def create_fix_script():
    """Create a script to fix the patterns"""
    print("\n" + "=" * 50)
    print("CREATING FIX SCRIPT")
    print("=" * 50)
    
    # First, let's get the exact patterns
    patterns_to_fix = []
    
    # 1. runtime.py - _RE_PROC_CALL
    try:
        with open('mini_basic/runtime.py', 'r') as f:
            content = f.read()
        # Find the _RE_PROC_CALL pattern
        import re
        match = re.search(r"_RE_PROC_CALL\s*=\s*re\.compile\(rf'\^\(self\._VAR_BASE_PATTERN\)\\s*\(\?:\((.*)\)\)\?\$'\)", content)
        if match:
            patterns_to_fix.append({
                'file': 'mini_basic/runtime.py',
                'pattern': "_RE_PROC_CALL = re.compile(rf'^({self._VAR_BASE_PATTERN})\\s*(?:\((.*)\))?$')",
                'replacement': "_RE_PROC_CALL = re.compile(rf'^(PROC_FN_NAME_PATTERN)\\s*(?:\((.*)\))?$')",
                'import_needed': True,
                'import_from': "from .expr.patterns import PROC_FN_NAME_PATTERN"
            })
    except Exception as e:
        print(f"Could not find _RE_PROC_CALL pattern: {e}")
    
    # 2. runtime.py - _RE_DEF_PROC
    try:
        with open('mini_basic/runtime.py', 'r') as f:
            content = f.read()
        # Find the _RE_DEF_PROC pattern
        match = re.search(r"_RE_DEF_PROC\s*=\s*re\.compile\(rf'\^\(self\._VAR_BASE_PATTERN\)\\s*\(\?:\((.*)\)\)\?\$'\)", content)
        if match:
            patterns_to_fix.append({
                'file': 'mini_basic/runtime.py',
                'pattern': "_RE_DEF_PROC = re.compile(rf'^({self._VAR_BASE_PATTERN})\\s*(?:\((.*)\))?$')",
                'replacement': "_RE_DEF_PROC = re.compile(rf'^(PROC_FN_NAME_PATTERN)\\s*(?:\((.*)\))?$')",
                'import_needed': False,  # Will be added by the first one if needed
                'import_from': None
            })
    except Exception as e:
        print(f"Could not find _RE_DEF_PROC pattern: {e}")
    
    # 3. expr/patterns.py - RE_FN_CALL
    try:
        with open('mini_basic/expr/patterns.py', 'r') as f:
            content = f.read()
        # Find the RE_FN_CALL pattern
        match = re.search(r"RE_FN_CALL\s*=\s*re\.compile\(rf'\^\({self\._VAR_BASE_PATTERN}\|\[0\-9\]\+\)\\s*\(\?:\((.*)\)\)\?\$'\)", content)
        if match:
            patterns_to_fix.append({
                'file': 'mini_basic/expr/patterns.py',
                'pattern': "RE_FN_CALL = re.compile(rf'^({self._VAR_BASE_PATTERN}|[0-9]+)\\s*(?:\((.*)\))?$')",
                'replacement': "RE_FN_CALL = re.compile(rf'^(PROC_FN_NAME_PATTERN)\\s*(?:\((.*)\))?$')",
                'import_needed': False,  # Defined in same file
                'import_from': None
            })
    except Exception as e:
        print(f"Could not find RE_FN_CALL pattern: {e}")
    
    # 4-6. runtime_parts/defs.py - Three instances of self._VAR_BASE_PATTERN
    try:
        with open('mini_basic/runtime_parts/defs.py', 'r') as f:
            content = f.read()
        # Find all instances of self._VAR_BASE_PATTERN in if self.matches(...) contexts
        matches = list(re.finditer(r"if\s+self\.matches\(self\._VAR_BASE_PATTERN\):", content))
        for i, match in enumerate(matches):
            patterns_to_fix.append({
                'file': 'mini_basic/runtime_parts/defs.py',
                'pattern': "if self.matches(self._VAR_BASE_PATTERN):",
                'replacement': "if self.matches(PROC_FN_NAME_PATTERN):",
                'import_needed': i == 0,  # Only need import for the first one
                'import_from': "from ..expr.patterns import PROC_FN_NAME_PATTERN"
            })
    except Exception as e:
        print(f"Could not find self._VAR_BASE_PATTERN patterns in defs.py: {e}")
    
    # 7. runtime_parts/program.py - _parse_proc_call pattern
    try:
        with open('mini_basic/runtime_parts/program.py', 'r') as f:
            content = f.read()
        # Find the pattern in _parse_proc_call
        match = re.search(r"rf'\^\({self\._VAR_BASE_PATTERN}\)\\s*\(\?:\((.*)\)\)\?\$'", content)
        if match:
            patterns_to_fix.append({
                'file': 'mini_basic/runtime_parts/program.py',
                'pattern': "rf'^({self._VAR_BASE_PATTERN})\\s*(?:\((.*)\))?$'",
                'replacement': "rf'^(PROC_FN_NAME_PATTERN)\\s*(?:\((.*)\))?$'",
                'import_needed': True,
                'import_from': "from ..expr.patterns import PROC_FN_NAME_PATTERN"
            })
    except Exception as e:
        print(f"Could not find _parse_proc_call pattern: {e}")
    
    # Show what we found
    print(f"Found {len(patterns_to_fix)} patterns to fix:")
    for i, p in enumerate(patterns_to_fix, 1):
        print(f"\n{i}. {p['file']}:")
        print(f"   Pattern: {p['pattern']}")
        print(f"   Replace with: {p['replacement']}")
        if p['import_needed']:
            print(f"   Import needed: {p['import_from']}")
    
    # Create the fix script
    fix_script = '''import os
import re

def apply_fixes():
    """Apply the fixes to replace repeated patterns with PROC_FN_NAME_PATTERN"""
    
    fixes = [
'''
    
    for i, fix in enumerate(patterns_to_fix):
        # Escape the pattern and replacement for use in the script
        pattern_escaped = repr(fix['pattern'])[1:-1]  # Remove the quotes from repr
        replacement_escaped = repr(fix['replacement'])[1:-1]
        
        fix_script += f'''    {{
        "file": r"{fix['file']}",
        "pattern": r"{pattern_escaped}",
        "replacement": r"{replacement_escaped}",
        "import_needed": {str(fix['import_needed']).lower()},
        "import_from": {repr(fix['import_from'])}
    }},
'''
    
    fix_script += '''    ]
    
    for fix in fixes:
        filepath = fix["file"]
        if not os.path.exists(filepath):
            print(f"File not found: {filepath}")
            continue
            
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Apply the replacement
            new_content, count = re.subn(fix["pattern"], fix["replacement"], content)
            
            if count > 0:
                # Add import if needed
                if fix["import_needed"] and fix["import_from"]:
                    import_line = fix["import_from"] + '\\n'
                    # Check if import already exists
                    if fix["import_from"] not in content:
                        # Find a good place to insert (after last import)
                        lines = new_content.split('\\n')
                        insert_at = 0
                        for i, line in enumerate(lines):
                            if line.strip().startswith('import ') or line.strip().startswith('from '):
                                insert_at = i + 1
                        # Insert the import
                        lines.insert(insert_at, import_line.rstrip())
                        new_content = '\\n'.join(lines)
                
                # Write the file
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(new_content)
                
                print(f"✓ Fixed {count} occurrence(s) in {filepath}")
                if fix["import_needed"] and fix["import_from"] and fix["import_from"] not in content:
                    print(f"  Added import: {fix['import_from']}")
            else:
                print(f"○ No changes needed in {filepath} (pattern may already be fixed)")
                
        except Exception as e:
            print(f"✗ Error processing {filepath}: {e}")

if __name__ == "__main__":
    print("Applying PROC/FN name pattern fixes...")
    apply_fixes()
    print("\\nDone!")
'''
    
    # Write the fix script
    with open('apply_fixes.py', 'w') as f:
        f.write(fix_script)
    
    print(f"\nFix script created: apply_fixes.py")
    print("Review the changes above, then run: python apply_fixes.py")

if __name__ == "__main__":
    show_current_patterns()
    create_fix_script()
