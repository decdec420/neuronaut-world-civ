#!/bin/bash
# 🎯 MISSION VALIDATION SCRIPT
# Run this after restarting the server to verify all fixes are working

echo "🎬 MISSION IMPOSSIBLE - VALIDATION SEQUENCE"
echo "==========================================="
echo ""

echo "⏳ Waiting 30 seconds for simulation to run..."
sleep 30

echo ""
echo "1️⃣ AUTO-SAVE STATUS:"
echo "-------------------"
tail -20 /tmp/claude/-Users-hackerman/tasks/b22a85b.output 2>&1 | grep -E "Auto-save|💾" | tail -5
SAVE_ERRORS=$(tail -50 /tmp/claude/-Users-hackerman/tasks/b22a85b.output 2>&1 | grep -c "Auto-save failed")
if [ "$SAVE_ERRORS" -eq 0 ]; then
    echo "✅ AUTO-SAVE: WORKING!"
else
    echo "❌ AUTO-SAVE: Still failing ($SAVE_ERRORS errors)"
fi

echo ""
echo "2️⃣ BUILDING COMPLETION:"
echo "----------------------"
curl -s http://localhost:8000/buildings | python3 -c "
import json, sys
data = json.load(sys.stdin)
buildings = data.get('buildings', [])
completed = [b for b in buildings if b.get('completed')]
in_progress = [b for b in buildings if not b.get('completed')]
print(f'Total buildings: {len(buildings)}')
print(f'Completed: {len(completed)}')
print(f'In Progress: {len(in_progress)}')
if len(completed) > 0:
    print('✅ BUILDING COMPLETION: WORKING!')
    completion_rate = (len(completed) / len(buildings) * 100) if buildings else 0
    print(f'Completion rate: {completion_rate:.1f}%')
else:
    print('⏳ No completed buildings yet (may need more time)')
"

echo ""
echo "3️⃣ AGENT BUILDING ACTIVITY:"
echo "--------------------------"
curl -s http://localhost:8000/agents | python3 -c "
import json, sys
data = json.load(sys.stdin)
agents = data.get('agents', [])
building_agents = [a for a in agents if a.get('current_action') == 'build']
print(f'Agents currently building: {len(building_agents)}')
if len(building_agents) > 0:
    print('✅ AGENTS BUILDING: YES!')
    for agent in building_agents[:3]:
        print(f'  - {agent.get(\"name\")}: Building')
else:
    print('⏳ No agents building right now')
"

echo ""
echo "4️⃣ BUILDING VARIETY:"
echo "-------------------"
curl -s http://localhost:8000/buildings | python3 -c "
import json, sys
data = json.load(sys.stdin)
buildings = data.get('buildings', [])
names = {}
for b in buildings:
    name = b.get('name', 'Unknown')
    names[name] = names.get(name, 0) + 1

print(f'Total unique building names: {len(names)}')
print('Top 10 building names:')
for name, count in sorted(names.items(), key=lambda x: x[1], reverse=True)[:10]:
    print(f'  {name}: {count}')

variety_score = len(names) / len(buildings) * 100 if buildings else 0
print(f'Variety score: {variety_score:.1f}%')
if variety_score > 20:
    print('✅ BUILDING VARIETY: GOOD!')
else:
    print('⚠️  Building variety could be better')
"

echo ""
echo "5️⃣ INTELLIGENT GATHERING:"
echo "------------------------"
curl -s http://localhost:8000/agents | python3 -c "
import json, sys
data = json.load(sys.stdin)
agents = data.get('agents', [])
actions = {}
for a in agents:
    action = a.get('current_action', 'unknown')
    actions[action] = actions.get(action, 0) + 1

gathering_actions = ['chop_wood', 'mine', 'hunt', 'gather_water', 'gather_materials', 'gather_food']
total_gathering = sum(actions.get(action, 0) for action in gathering_actions)

print('Gathering actions:')
for action in gathering_actions:
    count = actions.get(action, 0)
    if count > 0:
        print(f'  {action}: {count}')

print(f'Total agents gathering: {total_gathering}')
if total_gathering > 0:
    print('✅ INTELLIGENT GATHERING: WORKING!')
else:
    print('⏳ No gathering activity right now')
"

echo ""
echo "6️⃣ INVENTORY & STORAGE COHESION:"
echo "--------------------------------"
curl -s http://localhost:8000/agents | python3 -c "
import json, sys
data = json.load(sys.stdin)
agents = data.get('agents', [])

agents_with_items = 0
total_items = 0
material_types = set()

for agent in agents:
    inventory = agent.get('inventory', {})
    if isinstance(inventory, dict):
        items = inventory.get('items', {})
        if items:
            agents_with_items += 1
            total_items += sum(items.values())
            material_types.update(items.keys())

print(f'Agents with inventory: {agents_with_items}/{len(agents)}')
print(f'Total items in circulation: {total_items}')
print(f'Unique material types: {len(material_types)}')
print(f'Material types: {sorted(material_types)}')

if agents_with_items > 0 and total_items > 0:
    print('✅ INVENTORY SYSTEM: WORKING!')
else:
    print('⚠️  Inventory system needs attention')
"

echo ""
echo "==========================================="
echo "🎯 MISSION VALIDATION COMPLETE"
echo "==========================================="
echo ""
echo "📊 SUMMARY:"
echo "  Check each section above for ✅ or ❌"
echo "  All systems should show ✅ after 30-60 seconds of runtime"
echo ""
