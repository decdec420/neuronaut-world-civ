#!/usr/bin/env python3
"""
Script to remove Phase 2 perception sections from simulation.py.
These sections have been moved to PerceptionBuilder.
"""

def remove_perception_sections():
    """Remove all Phase 2 perception sections from simulation.py"""

    sim_path = '/sessions/affectionate-wizardly-ride/mnt/neuronaut-world/engine/simulation.py'

    # Read the file
    with open(sim_path, 'r') as f:
        lines = f.readlines()

    # Define sections to remove with their start/end markers
    sections_to_remove = [
        {
            'name': 'entertainment',
            'start': '# ===== ADD FUN/ENTERTAINMENT INFORMATION =====',
            'end': "perceptions['fun_info'] = fun_info"
        },
        {
            'name': 'consequences',
            'start': '# ===== ADD CONSEQUENCES INFORMATION =====',
            'end': "perceptions['consequences_info'] = consequences_info"
        },
        {
            'name': 'agriculture',
            'start': '# ===== ADD AGRICULTURE INFORMATION =====',
            'end': "perceptions['agriculture_info'] = agriculture_info"
        },
        {
            'name': 'health',
            'start': '# ===== ADD HEALTH & DISEASE INFORMATION =====',
            'end': "perceptions['health_info'] = health_info"
        },
        {
            'name': 'religion',
            'start': '# ===== ADD RELIGION INFORMATION =====',
            'end': "perceptions['religion_info'] = religion_info"
        },
        {
            'name': 'territory',
            'start': '# ===== ADD TERRITORY INFORMATION =====',
            'end': "perceptions['territory_info'] = territory_info"
        },
        {
            'name': 'chemistry',
            'start': '# ===== ADD CHEMISTRY INFORMATION =====',
            'end': "perceptions['chemistry_info'] = chemistry_info"
        },
        {
            'name': 'energy',
            'start': '# ===== ADD ENERGY INFORMATION =====',
            'end': "perceptions['energy_info'] = energy_info"
        },
        {
            'name': 'materials',
            'start': '# ===== ADD MATERIALS SCIENCE INFORMATION =====',
            'end': "perceptions['materials_info'] = materials_info"
        },
        {
            'name': 'life',
            'start': '# ===== ADD LIFE & REPRODUCTION INFORMATION =====',
            'end': "perceptions['life_info'] = life_info"
        },
        {
            'name': 'economic',
            'start': '# ===== ADD ECONOMIC & FINANCIAL INFORMATION =====',
            'end': "perceptions['economic_info'] = economic_info"
        }
    ]

    # Process each section
    for section in sections_to_remove:
        start_marker = section['start']
        end_marker = section['end']

        # Find start and end indices
        start_idx = None
        end_idx = None

        for i, line in enumerate(lines):
            if start_marker in line:
                start_idx = i
            if start_idx is not None and end_marker in line:
                end_idx = i
                break

        if start_idx is not None and end_idx is not None:
            # Replace section with a comment
            comment = f"            # {section['name'].upper()} INFO - Moved to PerceptionBuilder\n"
            lines[start_idx:end_idx+1] = [comment]
            print(f"✓ Removed {section['name']} section (lines {start_idx+1}-{end_idx+1})")
        else:
            print(f"✗ Could not find {section['name']} section")

    # Write back
    with open(sim_path, 'w') as f:
        f.writelines(lines)

    print("\n✅ Phase 2 complete! All perception sections moved to PerceptionBuilder")
    print(f"📝 Updated: {sim_path}")

if __name__ == '__main__':
    remove_perception_sections()
