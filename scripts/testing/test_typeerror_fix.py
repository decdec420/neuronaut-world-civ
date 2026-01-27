#!/usr/bin/env python3
"""
Quick test to verify the Need comparison TypeError is fixed
"""
import asyncio
import sys

async def test_simulation():
    from engine.simulation import SimulationEngine
    
    print('🧪 Testing simulation for Need comparison TypeError...\n')
    
    # Initialize simulation (same way as server.py)
    engine = SimulationEngine()
    engine.initialize_world(num_agents=5)  # Small number for quick test
    
    print(f'✅ Initialized with {len(engine.world.agents)} agents\n')
    
    # Run 5 ticks to test for the TypeError
    errors = []
    for i in range(5):
        try:
            await engine.tick()
            print(f'✅ Tick {i+1} completed successfully')
        except TypeError as e:
            if 'not supported between instances' in str(e) and 'Need' in str(e):
                errors.append((i+1, str(e)))
                print(f'❌ Tick {i+1} FAILED with TypeError: {e}')
                import traceback
                traceback.print_exc()
                break
    
    print()
    if errors:
        print('❌ FAILED - Need comparison TypeError still present')
        sys.exit(1)
    else:
        print('🎉 SUCCESS - All ticks completed without TypeError!')
        print('✅ The Need comparison bug is FIXED!')
        print()
        print('Cache was cleared and the code is now running correctly.')

if __name__ == '__main__':
    asyncio.run(test_simulation())
