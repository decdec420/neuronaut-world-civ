#!/usr/bin/env python3
"""
Fixed version of audit repair script
"""

def fix_simulation_file():
    with open('engine/simulation.py', 'r') as f:
        lines = f.readlines()
    
    changes = []
    
    # Process line by line
    for i, line in enumerate(lines):
        line_num = i + 1
        
        # Fix 1: Line 2572 - Remove duplicate NeedType import
        if line_num == 2572 and 'from agents.agent import NeedType' in line:
            lines[i] = line.replace('from agents.agent import NeedType', 
                                   '# NeedType already imported at top of file')
            changes.append(f"Line {line_num}: Removed duplicate NeedType import")
        
        # Fix 2: Line 1654 - Unsafe needs access
        if line_num == 1654 and "if agent.needs.needs[NeedType.HUNGER].level < 0.3:" in line:
            indent = len(line) - len(line.lstrip())
            lines[i] = ' ' * indent + "hunger_need = agent.needs.needs.get(NeedType.HUNGER)\n"
            lines.insert(i+1, ' ' * indent + "if hunger_need and hunger_need.level < 0.3:\n")
            changes.append(f"Line {line_num}: Made HUNGER need access safe")
        
        # Fix 3: Line 1657 - Unsafe needs access  
        if line_num == 1657 and "elif agent.needs.needs[NeedType.THIRST].level < 0.3:" in line:
            indent = len(line) - len(line.lstrip())
            lines[i] = ' ' * indent + "thirst_need = agent.needs.needs.get(NeedType.THIRST)\n"
            lines.insert(i+1, ' ' * indent + "elif thirst_need and thirst_need.level < 0.3:\n")
            changes.append(f"Line {line_num}: Made THIRST need access safe")
        
        # Fix 4: Lines 1908-1910 - Unsafe needs access
        if line_num == 1908 and "if agent.needs.needs[NeedType.HUNGER].level > 0.5:" in line:
            indent = len(line) - len(line.lstrip())
            lines[i] = ' ' * indent + "hunger_need = agent.needs.needs.get(NeedType.HUNGER)\n"
            lines.insert(i+1, ' ' * indent + "if hunger_need and hunger_need.level > 0.5:\n")
            changes.append(f"Line {line_num}: Made HUNGER need access safe in scarcity check")
        
        if line_num == 1910 and "if agent.needs.needs[NeedType.THIRST].level > 0.5:" in line:
            indent = len(line) - len(line.lstrip())
            lines[i] = ' ' * indent + "thirst_need = agent.needs.needs.get(NeedType.THIRST)\n"
            lines.insert(i+1, ' ' * indent + "if thirst_need and thirst_need.level > 0.5:\n")
            changes.append(f"Line {line_num}: Made THIRST need access safe in scarcity check")
        
        # Fix 5: Line 3472 - Unsafe hunger access
        if "hunger_before = agent.needs.needs[NeedType.HUNGER].level" in line:
            indent = len(line) - len(line.lstrip())
            lines[i] = ' ' * indent + "hunger_need = agent.needs.needs.get(NeedType.HUNGER)\n"
            lines.insert(i+1, ' ' * indent + "hunger_before = hunger_need.level if hunger_need else 0.0\n")
            changes.append(f"Line {line_num}: Made hunger_before safe")
        
        # Fix 6: Line 3475 - Unsafe hunger access
        if "hunger_after = agent.needs.needs[NeedType.HUNGER].level" in line and "hunger_need" not in line:
            indent = len(line) - len(line.lstrip())
            lines[i] = ' ' * indent + "hunger_after = hunger_need.level if hunger_need else 0.0\n"
            changes.append(f"Line {line_num}: Made hunger_after safe")
        
        # Fix 7: Line 6143 - Unsafe SAFETY need access
        if "agent.needs.needs[NeedType.SAFETY].level = min(" in line:
            indent = len(line) - len(line.lstrip())
            lines[i] = ' ' * indent + "safety_need = agent.needs.needs.get(NeedType.SAFETY)\n"
            lines.insert(i+1, ' ' * indent + "if safety_need:\n")
            lines.insert(i+2, ' ' * (indent+4) + "safety_need.level = min(\n")
            lines.insert(i+3, ' ' * (indent+8) + "1.0,\n")
            lines.insert(i+4, ' ' * (indent+8) + "safety_need.level + (effects.agent_damage / 100.0)\n")
            lines.insert(i+5, ' ' * (indent+4) + ")\n")
            changes.append(f"Line {line_num}: Made SAFETY need access safe")
        
        # Fix 8: Line 3320 - Division by zero
        if "avg_age_at_death = sum(a.age for a in recent_deaths) / len(recent_deaths)" in line:
            lines[i] = line.replace("/ len(recent_deaths)", "/ max(1, len(recent_deaths))")
            changes.append(f"Line {line_num}: Protected against division by zero")
        
        # Fix 9: Line 6253 - Division by zero
        if "sum(positive_changes) / len(positive_changes)" in line:
            lines[i] = line.replace("/ len(positive_changes)", "/ max(1, len(positive_changes))")
            changes.append(f"Line {line_num}: Protected against division by zero")
    
    with open('engine/simulation.py', 'w') as f:
        f.writelines(lines)
    
    return changes

if __name__ == '__main__':
    print("Applying fixes to engine/simulation.py...")
    changes = fix_simulation_file()
    
    if changes:
        print(f"\nApplied {len(changes)} fixes:")
        for change in changes:
            print(f"  ✓ {change}")
    else:
        print("No changes applied")
