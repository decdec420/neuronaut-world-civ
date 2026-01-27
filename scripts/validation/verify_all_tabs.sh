#!/bin/bash
# Final verification of all 15 tab endpoints

echo "=== COMPLETE TAB ENDPOINT VERIFICATION ==="
echo

endpoints=(
  "world:🌍 World View"
  "agents:👥 Agents"
  "experiments:⚗️ Experimentation"
  "buildings:🏛️ Infrastructure"
  "knowledge:📚 Knowledge"
  "consequences:⚠️ Consequences"
  "roles:👷 Roles"
  "economy:💰 Economy"
  "innovations:🚀 Tech Progression"
  "events:📜 Events"
  "stories:📖 Stories"
  "achievements:🏆 Achievements"
  "culture:🎉 Culture"
  "politics:🏛️ Politics"
  "conflicts:⚔️ Conflicts"
)

passed=0
failed=0

for item in "${endpoints[@]}"; do
  IFS=':' read -r ep name <<< "$item"
  code=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:8000/$ep")
  
  if [ "$code" = "200" ]; then
    echo "✅ $name → /$ep"
    ((passed++))
  else
    echo "❌ $name → /$ep ($code)"
    ((failed++))
  fi
done

echo
echo "=========================================="
echo "Summary: $passed/15 tabs working perfectly!"
echo "=========================================="
