#!/usr/bin/env python3
"""
Comprehensive Audit Fix Script for Neuronaut World
Fixes all identified issues in simulation.py
"""

import re
import sys

def fix_simulation_file():
    """Fix all issues in engine/simulation.py"""
    
    with open('engine/simulation.py', 'r') as f:
        content = f.read()
    
    original_content = content
    
    # Issue 1: Remove duplicate NeedType import at line 2572
    # This import is inside an if block but NeedType is already imported at top
    content = re.sub(
        r'(\s+)elif hasattr\(agent, \'needs\'\) and hasattr\(agent\.needs, \'needs\'\):\s*\n\s+# Check if they need social interaction or fun\s*\n\s+from agents\.agent import NeedType',
        r'\1elif hasattr(agent, \'needs\') and hasattr(agent.needs, \'needs\'):\n\1    # Check if they need social interaction or fun (using NeedType from top-level import)',
        content
    )
    
    # Issue 2: Fix unsafe agent.needs.needs[NeedType.X].level accesses
    # Replace with safe .get() pattern
    
    # Pattern at line 1654: agent.needs.needs[NeedType.HUNGER].level < 0.3
    content = re.sub(
        r'if agent\.needs\.needs\[NeedType\.HUNGER\]\.level < 0\.3:',
        r'if hasattr(agent, \'needs\') and agent.needs.needs.get(NeedType.HUNGER) and agent.needs.needs[NeedType.HUNGER].level < 0.3:',
        content
    )
    
    # Pattern at line 1657: agent.needs.needs[NeedType.THIRST].level < 0.3
    content = re.sub(
        r'elif agent\.needs\.needs\[NeedType\.THIRST\]\.level < 0\.3:',
        r'elif hasattr(agent, \'needs\') and agent.needs.needs.get(NeedType.THIRST) and agent.needs.needs[NeedType.THIRST].level < 0.3:',
        content
    )
    
    # Pattern at lines 1908-1910: agent.needs.needs[NeedType.HUNGER/THIRST].level > 0.5
    content = re.sub(
        r'(\s+)if agent\.needs\.needs\[NeedType\.HUNGER\]\.level > 0\.5:',
        r'\1if hasattr(agent, \'needs\') and agent.needs.needs.get(NeedType.HUNGER) and agent.needs.needs[NeedType.HUNGER].level > 0.5:',
        content
    )
    content = re.sub(
        r'(\s+)if agent\.needs\.needs\[NeedType\.THIRST\]\.level > 0\.5:',
        r'\1if hasattr(agent, \'needs\') and agent.needs.needs.get(NeedType.THIRST) and agent.needs.needs[NeedType.THIRST].level > 0.5:',
        content
    )
    
    # Pattern at line 3472-3475: hunger_before/after
    content = re.sub(
        r'hunger_before = agent\.needs\.needs\[NeedType\.HUNGER\]\.level',
        r'hunger_before = agent.needs.needs.get(NeedType.HUNGER).level if agent.needs.needs.get(NeedType.HUNGER) else 0.0',
        content
    )
    content = re.sub(
        r'hunger_after = agent\.needs\.needs\[NeedType\.HUNGER\]\.level',
        r'hunger_after = agent.needs.needs.get(NeedType.HUNGER).level if agent.needs.needs.get(NeedType.HUNGER) else 0.0',
        content
    )
    
    # Pattern at line 6143-6145: agent.needs.needs[NeedType.SAFETY].level
    content = re.sub(
        r'agent\.needs\.needs\[NeedType\.SAFETY\]\.level = min\(\s*1\.0,\s*agent\.needs\.needs\[NeedType\.SAFETY\]\.level \+ \(effects\.agent_damage / 100\.0\)\s*\)',
        r'if agent.needs.needs.get(NeedType.SAFETY):\n                            agent.needs.needs[NeedType.SAFETY].level = min(\n                                1.0,\n                                agent.needs.needs[NeedType.SAFETY].level + (effects.agent_damage / 100.0)\n                            )',
        content
    )
    
    # Issue 3: Fix division by zero at line 3320
    content = re.sub(
        r'if recent_deaths:\s*\n\s+avg_age_at_death = sum\(a\.age for a in recent_deaths\) / len\(recent_deaths\)',
        r'if recent_deaths:\n                avg_age_at_death = sum(a.age for a in recent_deaths) / max(1, len(recent_deaths))',
        content
    )
    
    # Issue 4: Fix division by zero at line 6253
    content = re.sub(
        r'if positive_changes:\s*\n\s+need_satisfaction_score = min\(1\.0, sum\(positive_changes\) / len\(positive_changes\) \* 2\.0\)',
        r'if positive_changes:\n                need_satisfaction_score = min(1.0, sum(positive_changes) / max(1, len(positive_changes)) * 2.0)',
        content
    )
    
    if content != original_content:
        with open('engine/simulation.py', 'w') as f:
            f.write(content)
        print("✓ Fixed engine/simulation.py")
        return True
    else:
        print("⚠ No changes needed in engine/simulation.py")
        return False

def check_other_files():
    """Check other files for similar issues"""
    files_to_check = [
        'world/conflict.py',
        'agents/strategy.py', 
        'agents/llm_brain.py',
        'agents/autonomous_agent.py',
        'engine/action_handlers.py'
    ]
    
    issues_found = []
    
    for filepath in files_to_check:
        try:
            with open(filepath, 'r') as f:
                content = f.read()
                lines = content.split('\n')
                
            for i, line in enumerate(lines, 1):
                # Check for scoped NeedType imports
                if 'from engine.psychology import NeedType' in line or 'from agents.agent import NeedType' in line:
                    # Check if it's not in the first 50 lines (likely scoped)
                    if i > 50:
                        issues_found.append(f"{filepath}:{i}: NeedType imported inside scope")
                
                # Check for unsafe .needs.needs[] access
                if '.needs.needs[NeedType.' in line and '.get(' not in line:
                    issues_found.append(f"{filepath}:{i}: Unsafe needs dictionary access")
                    
        except FileNotFoundError:
            issues_found.append(f"{filepath}: File not found")
    
    return issues_found

if __name__ == '__main__':
    print("=" * 70)
    print("NEURONAUT WORLD - COMPREHENSIVE AUDIT & FIX")
    print("=" * 70)
    print()
    
    # Fix simulation.py
    print("1. Fixing engine/simulation.py...")
    fix_simulation_file()
    print()
    
    # Check other files
    print("2. Checking other files for similar issues...")
    other_issues = check_other_files()
    if other_issues:
        print(f"   Found {len(other_issues)} potential issues:")
        for issue in other_issues:
            print(f"   - {issue}")
    else:
        print("   ✓ No issues found in other files")
    print()
    
    print("=" * 70)
    print("AUDIT COMPLETE")
    print("=" * 70)
