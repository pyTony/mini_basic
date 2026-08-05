import os
import re

def apply_fixes():
    """Apply the fixes to replace repeated patterns with PROC_FN_NAME_PATTERN"""
    
    fixes = [
    ]
    
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
                    import_line = fix["import_from"] + '\n'
                    # Check if import already exists
                    if fix["import_from"] not in content:
                        # Find a good place to insert (after last import)
                        lines = new_content.split('\n')
                        insert_at = 0
                        for i, line in enumerate(lines):
                            if line.strip().startswith('import ') or line.strip().startswith('from '):
                                insert_at = i + 1
                        # Insert the import
                        lines.insert(insert_at, import_line.rstrip())
                        new_content = '\n'.join(lines)
                
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
    print("\nDone!")
