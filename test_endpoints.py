#!/usr/bin/env python3
"""
Verify all tab endpoints are properly connected
"""
import requests
import json

# Map visible tabs to their API endpoints
tab_endpoints = {
    '🌍 World View': '/world',
    '👥 Agents': '/agents',
    '🔬 Experimentation': '/experiments',
    '🏛️ Infrastructure': '/buildings',
    '📚 Knowledge': '/knowledge',
    '⚠️ Consequences': '/consequences',
    '🎭 Roles': '/roles',
    '💰 Economy': '/economy',
    '🚀 Tech Progression': '/innovations',
    '📜 Events': '/events',
    '📖 Stories': '/stories',
    '🏆 Achievements': '/achievements'
}

def test_endpoint(base_url, endpoint):
    """Test if an endpoint is working"""
    try:
        response = requests.get(f'{base_url}{endpoint}', timeout=3)
        return response.status_code, response.json() if response.status_code == 200 else None
    except requests.exceptions.ConnectionError:
        return 'CONNECTION_ERROR', None
    except requests.exceptions.Timeout:
        return 'TIMEOUT', None
    except Exception as e:
        return f'ERROR: {str(e)[:30]}', None

def main():
    base_url = 'http://localhost:8000'
    
    print('=' * 70)
    print('🔍 ENDPOINT CONNECTIVITY VERIFICATION')
    print('=' * 70)
    print()
    
    results = {
        'passed': [],
        'failed': [],
        'connection_error': []
    }
    
    for tab_name, endpoint in tab_endpoints.items():
        status, data = test_endpoint(base_url, endpoint)
        
        if status == 'CONNECTION_ERROR':
            print(f'🔌 {tab_name:30} → {endpoint:20} [Server not running]')
            results['connection_error'].append((tab_name, endpoint))
        elif status == 200:
            # Check if data is valid
            data_preview = ''
            if isinstance(data, dict):
                keys = list(data.keys())[:3]
                data_preview = f" ({', '.join(keys)}...)"
            elif isinstance(data, list):
                data_preview = f" ({len(data)} items)"
            
            print(f'✅ {tab_name:30} → {endpoint:20} [OK]{data_preview}')
            results['passed'].append((tab_name, endpoint))
        else:
            print(f'❌ {tab_name:30} → {endpoint:20} [Status: {status}]')
            results['failed'].append((tab_name, endpoint, status))
    
    print()
    print('=' * 70)
    print('📊 SUMMARY')
    print('=' * 70)
    
    total = len(tab_endpoints)
    passed = len(results['passed'])
    failed = len(results['failed'])
    conn_error = len(results['connection_error'])
    
    if conn_error > 0:
        print(f'🔌 Server Connection: Not running (test localhost:8000)')
        print(f'   Start with: python3 main.py')
    elif passed == total:
        print(f'✅ All {total} endpoints working perfectly!')
    else:
        print(f'✅ Working: {passed}/{total}')
        print(f'❌ Failed: {failed}/{total}')
        
        if failed > 0:
            print()
            print('Failed endpoints:')
            for tab, endpoint, status in results['failed']:
                print(f'  - {endpoint} (Status: {status})')
    
    print()
    
    return 0 if failed == 0 else 1

if __name__ == '__main__':
    exit(main())
