#!/usr/bin/env python3
"""
Comprehensive Neuronaut World Codebase Audit & Fix
Fixes all identified issues systematically
"""

def fix_simulation_py():
    """Apply all fixes to engine/simulation.py"""
    with open('engine/simulation.py', 'r') as f:
        lines = f.readlines()
    
    fixes_applied = []
    i = 0
    while i < len(lines):
        line = lines[i]
        line_num = i + 1
        
        # Fix 1: Remove duplicate NeedType import at line ~2572
        if 'from agents.agent import NeedType' in line and line_num > 100:
            indent = len(line) - len(line.lstrip())
            lines[i] = ' ' * indent + '# NeedType already imported at module level\n'
            fixes_applied.append(f"Line {line_num}: Removed duplicate NeedType import")
        
        # Fix 2-5: Unsafe agent.needs.needs[NeedType.X].level access
        # These need safe .get() checks
        
        # Pattern: if agent.needs.needs[NeedType.HUNGER].level
        if 'if agent.needs.needs[NeedType.HUNGER].level' in line and '.get(' not in line:
            indent = len(line) - len(line.lstrip())
            condition = line.strip().split('if ')[1]
            lines[i] = ' ' * indent + f'hunger_need = agent.needs.needs.get(NeedType.HUNGER)\n'
            lines.insert(i+1, ' ' * indent + f'if hunger_need and hunger_need.level' + condition.split('.level')[1] + '\n')
            fixes_applied.append(f"Line {line_num}: Made HUNGER need access safe")
            i += 1  # Skip the inserted line
        
        # Pattern: elif agent.needs.needs[NeedType.THIRST].level
        elif 'elif agent.needs.needs[NeedType.THIRST].level' in line and '.get(' not in line:
            indent = len(line) - len(line.lstrip())
            condition = line.strip().split('elif ')[1]
            lines[i] = ' ' * indent + f'thirst_need = agent.needs.needs.get(NeedType.THIRST)\n'
            lines.insert(i+1, ' ' * indent + f'elif thirst_need and thirst_need.level' + condition.split('.level')[1] + '\n')
            fixes_applied.append(f"Line {line_num}: Made THIRST need access safe")
            i += 1
        
        # Pattern: hunger_before = agent.needs.needs[NeedType.HUNGER].level
        elif 'hunger_before = agent.needs.needs[NeedType.HUNGER].level' in line:
            indent = len(line) - len(line.lstrip())
            lines[i] = ' ' * indent + 'hunger_need = agent.needs.needs.get(NeedType.HUNGER)\n'
            lines.insert(i+1, ' ' * indent + 'hunger_before = hunger_need.level if hunger_need else 0.0\n')
            fixes_applied.append(f"Line {line_num}: Made hunger_before safe")
            i += 1
        
        # Pattern: hunger_after = agent.needs.needs[NeedType.HUNGER].level
        elif 'hunger_after = agent.needs.needs[NeedType.HUNGER].level' in line and 'hunger_need' not in line:
            indent = len(line) - len(line.lstrip())
            lines[i] = ' ' * indent + 'hunger_after = hunger_need.level if hunger_need else 0.0\n'
            fixes_applied.append(f"Line {line_num}: Made hunger_after safe")
        
        # Pattern: agent.needs.needs[NeedType.SAFETY].level = min(
        elif 'agent.needs.needs[NeedType.SAFETY].level = min(' in line:
            indent = len(line) - len(line.lstrip())
            # Replace with safe access
            lines[i] = ' ' * indent + 'safety_need = agent.needs.needs.get(NeedType.SAFETY)\n'
            lines.insert(i+1, ' ' * indent + 'if safety_need:\n')
            lines.insert(i+2, ' ' * (indent+4) + 'safety_need.level = min(\n')
            lines.insert(i+3, ' ' * (indent+8) + '1.0,\n')
            lines.insert(i+4, ' ' * (indent+8) + 'safety_need.level + (effects.agent_damage / 100.0)\n')
            lines.insert(i+5, ' ' * (indent+4) + ')\n')
            fixes_applied.append(f"Line {line_num}: Made SAFETY need assignment safe")
            i += 5
        
        # Fix 6: Division by zero - avg_age_at_death
        elif 'sum(a.age for a in recent_deaths) / len(recent_deaths)' in line:
            lines[i] = line.replace('/ len(recent_deaths)', '/ max(1, len(recent_deaths))')
            fixes_applied.append(f"Line {line_num}: Protected division by len(recent_deaths)")
        
        # Fix 7: Division by zero - positive_changes
        elif 'sum(positive_changes) / len(positive_changes)' in line:
            lines[i] = line.replace('/ len(positive_changes)', '/ max(1, len(positive_changes))')
            fixes_applied.append(f"Line {line_num}: Protected division by len(positive_changes)")
        
        i += 1
    
    # Write fixed file
    with open('engine/simulation.py', 'w') as f:
        f.writelines(lines)
    
    return fixes_applied

def audit_other_files():
    """Audit and report issues in other files"""
    files_to_check = {
        'agents/llm_brain.py': [],
        'agents/autonomous_agent.py': [],
        'engine/action_handlers.py': [],
        'world/conflict.py': [],
        'agents/strategy.py': []
    }
    
    for filepath in files_to_check.keys():
        try:
            with open(filepath, 'r') as f:
                lines = f.readlines()
            
            for i, line in enumerate(lines, 1):
                # Check for scoped imports
                if ('from engine.psychology import NeedType' in line or 
                    'from agents.agent import NeedType' in line) and i > 50:
                    files_to_check[filepath].append(
                        f"Line {i}: NeedType imported inside function/scope")
                
                # Check for unsafe needs access
                if '.needs.needs[NeedType.' in line and '.get(' not in lines[max(0,i-2):i+1]:
                    files_to_check[filepath].append(
                        f"Line {i}: Unsafe dictionary access to agent.needs.needs[]")
                
                # Check for division by len() without protection
                if '/ len(' in line and 'max(' not in line:
                    files_to_check[filepath].append(
                        f"Line {i}: Potential division by zero with len()")
        
        except FileNotFoundError:
            files_to_check[filepath].append("File not found")
    
    return files_to_check

if __name__ == '__main__':
    print("="*80)
    print("NEURONAUT WORLD - COMPREHENSIVE CODEBASE AUDIT & HEALTHCHECK")
    print("="*80)
    print()
    
    # Fix simulation.py
    print("1. FIXING engine/simulation.py")
    print("-" * 80)
    fixes = fix_simulation_py()
    if fixes:
        print(f"Applied {len(fixes)} fixes:")
        for fix in fixes:
            print(f"   ✓ {fix}")
    else:
        print("   No fixes needed (file already clean)")
    print()
    
    # Audit other files
    print("2. AUDITING OTHER FILES")
    print("-" * 80)
    audit_results = audit_other_files()
    
    total_issues = sum(len(issues) for issues in audit_results.values())
    if total_issues > 0:
        print(f"Found {total_issues} potential issues across {len([f for f, i in audit_results.items() if i])} files:\n")
        for filepath, issues in audit_results.items():
            if issues:
                print(f"   {filepath}:")
                for issue in issues:
                    print(f"      ⚠ {issue}")
                print()
    else:
        print("   ✓ No issues found in other files")
    
    print()
    print("="*80)
    print("AUDIT COMPLETE")
    print("="*80)
    print("\nSUMMARY:")
    print(f"  - Fixed {len(fixes)} issues in engine/simulation.py")
    print(f"  - Found {total_issues} additional issues requiring manual review")
    
    if total_issues > 0:
        print("\nRECOMMENDATIONS:")
        print("  1. Move all NeedType imports to module level")
        print("  2. Replace unsafe .needs.needs[] access with .get() checks")
        print("  3. Protect all division operations with max(1, len(...))")
