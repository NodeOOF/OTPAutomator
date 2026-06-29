import requests
import json
import re
import os
import time
from datetime import datetime

PHONE = input("Number : ")
API_FILE = 'api.txt'
RESULT_FILE = 'result.txt'


class APITester:
    def __init__(self, phone):
        self.phone = phone
        self.apis = {}
        self.results = []
        self.session = requests.Session()
        self.shared_data = {}
        self.tested_apis = set()

    def parse_api_file(self, filepath):
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        blocks = re.split(r'\n(?=\[)', content)
        for block in blocks:
            block = block.strip()
            if not block:
                continue

            match = re.match(r'\[([^\]]+)\]', block)
            if not match:
                continue

            api_id = match.group(1)
            api_config = {'id': api_id}

            for key in ('name', 'url', 'method', 'body', 'warmup', 'depends_on', 'extract_nonce', 'expected_fields'):
                pattern = rf'^{key}\s*=\s*(.+)$'
                km = re.search(pattern, block, re.MULTILINE)
                if km:
                    val = km.group(1).strip()
                    api_config[key] = val

            headers_match = re.search(r'^headers\s*=\s*\{', block, re.MULTILINE)
            if headers_match:
                start = headers_match.end() - 1
                brace_count = 0
                end = start
                for i in range(start, len(block)):
                    if block[i] == '{':
                        brace_count += 1
                    elif block[i] == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end = i + 1
                            break
                headers_str = block[start:end]
                try:
                    api_config['headers'] = json.loads(headers_str)
                except json.JSONDecodeError:
                    api_config['headers'] = {}

            self.apis[api_id] = api_config

    def interpolate(self, template):
        result = template
        result = result.replace('{{phone}}', self.phone)
        for key, val in self.shared_data.items():
            result = result.replace('{{' + key + '}}', str(val))
        return result

    def test_api(self, api_id):
        api = self.apis[api_id]
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        result = {
            'api_id': api_id,
            'name': api.get('name', api_id),
            'url': api.get('url', ''),
            'method': api.get('method', 'GET'),
            'timestamp': timestamp,
            'status': 'UNKNOWN',
            'status_code': 0,
            'response_body': '',
            'error': None,
        }

        # Warmup if needed
        if 'warmup' in api:
            warmup_url = self.interpolate(api['warmup'])
            try:
                resp = self.session.get(warmup_url, timeout=15)
                # Extract nonces from page if specified
                if 'extract_nonce' in api:
                    for nonce_name in api['extract_nonce'].split(','):
                        nonce_name = nonce_name.strip()
                        nonce_match = re.search(
                            rf'id="{nonce_name}"[^>]*value="([^"]+)"', resp.text)
                        if not nonce_match:
                            nonce_match = re.search(
                                rf'"{nonce_name}"\s*:\s*"([^"]+)"', resp.text)
                        if nonce_match:
                            self.shared_data[nonce_name] = nonce_match.group(1)
            except Exception:
                pass

        # Check dependencies
        if 'depends_on' in api:
            dep = api['depends_on']
            if dep not in self.tested_apis:
                result['status'] = 'SKIPPED'
                result['error'] = f'Dependency {dep} not satisfied'
                return result

        # Build request
        url = self.interpolate(api.get('url', ''))
        method = api.get('method', 'GET').upper()
        headers = {k: self.interpolate(v) for k, v in api.get('headers', {}).items()}

        body = None
        is_form = False
        if 'body' in api:
            body_str = self.interpolate(api['body'])
            # Strip surrounding quotes if present
            if (body_str.startswith('"') and body_str.endswith('"')) or \
               (body_str.startswith("'") and body_str.endswith("'")):
                body_str = body_str[1:-1]
            # Check if content-type is form-urlencoded
            ct = headers.get('Content-Type', '')
            if 'application/x-www-form-urlencoded' in ct:
                is_form = True
                body = dict(re.split(r'(?<!\\)=', part, 1) for part in body_str.split('&') if '=' in part)
            else:
                try:
                    body = json.loads(body_str)
                except json.JSONDecodeError:
                    body = body_str

        # Send request
        try:
            if method == 'POST':
                resp = self.session.post(url, data=body if is_form else None,
                                         json=body if not is_form else None,
                                         headers=headers, timeout=15)
            elif method == 'PUT':
                resp = self.session.put(url, data=body if is_form else None,
                                        json=body if not is_form else None,
                                        headers=headers, timeout=15)
            elif method == 'PATCH':
                resp = self.session.patch(url, data=body if is_form else None,
                                          json=body if not is_form else None,
                                          headers=headers, timeout=15)
            else:
                resp = self.session.get(url, headers=headers, timeout=15)

            result['status_code'] = resp.status_code

            try:
                result['response_body'] = resp.json()
            except Exception:
                result['response_body'] = resp.text[:2000]

            # Check success
            if resp.status_code == 200:
                result['status'] = 'SUCCESS'
            elif 200 <= resp.status_code < 300:
                result['status'] = 'SUCCESS'
            elif resp.status_code in (400, 401, 422):
                # Check if it's a rate limit (endpoint works but too fast)
                resp_text = str(result['response_body'])
                if 'seconds' in resp_text.lower() or 'rate' in resp_text.lower():
                    result['status'] = 'RATE_LIMIT'
                    result['error'] = 'Rate limited - endpoint works'
                else:
                    result['status'] = 'FAILED'
                    result['error'] = 'Bad Request - check parameters'
            elif resp.status_code == 403:
                result['status'] = 'BLOCKED'
                result['error'] = 'Forbidden - WAF/rate limit'
            elif resp.status_code == 404:
                result['status'] = 'NOT_FOUND'
                result['error'] = 'Endpoint not found'
            else:
                result['status'] = 'ERROR'
                result['error'] = f'HTTP {resp.status_code}'

            # Store shared data from response
            if isinstance(result['response_body'], dict):
                res = result['response_body'].get('result', {})
                for key in ('tempToken', 'token', 'code', 'otp'):
                    if key in res:
                        self.shared_data[key] = res[key]

            # Mark as tested
            self.tested_apis.add(api_id)

        except requests.exceptions.Timeout:
            result['status'] = 'TIMEOUT'
            result['error'] = 'Request timed out (15s)'
        except requests.exceptions.ConnectionError as e:
            result['status'] = 'CONN_ERROR'
            result['error'] = str(e)[:200]
        except Exception as e:
            result['status'] = 'ERROR'
            result['error'] = str(e)[:200]

        return result

    def run_all(self):
        print(f'=== API Test Suite - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} ===')
        print(f'Phone: {self.phone}')
        print(f'APIs found: {len(self.apis)}\n')

        # Determine test order (respect dependencies)
        tested = set()
        ordered = []

        def resolve(api_id):
            if api_id in tested:
                return
            api = self.apis.get(api_id, {})
            if 'depends_on' in api:
                resolve(api['depends_on'])
            ordered.append(api_id)
            tested.add(api_id)

        for api_id in self.apis:
            resolve(api_id)

        # Run tests
        for api_id in ordered:
            print(f'[{api_id}] Testing {self.apis[api_id].get("name", api_id)} ...')
            result = self.test_api(api_id)
            self.results.append(result)

            status_icon = {
                'SUCCESS': '[OK]',
                'RATE_LIMIT': '[RATE_LIMIT]',
                'FAILED': '[FAIL]',
                'BLOCKED': '[BLOCKED]',
                'SKIPPED': '[SKIP]',
                'TIMEOUT': '[TIMEOUT]',
                'CONN_ERROR': '[CONN_ERR]',
                'NOT_FOUND': '[404]',
            }.get(result['status'], '[??]')

            print(f'  {status_icon} {result["status"]} (HTTP {result["status_code"]})')
            if result['error']:
                print(f'       Error: {result["error"]}')
            if isinstance(result['response_body'], dict):
                print(f'       Response: {json.dumps(result["response_body"], ensure_ascii=False)[:200]}')
            print()

        return self.results

    def save_results(self, filepath):
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f'=== API Test Results ===\n')
            f.write(f'Date: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
            f.write(f'Phone: {self.phone}\n')
            f.write(f'Total: {len(self.results)}\n\n')

            passed = sum(1 for r in self.results if r['status'] == 'SUCCESS')
            rate_limited = sum(1 for r in self.results if r['status'] == 'RATE_LIMIT')
            failed = sum(1 for r in self.results if r['status'] in ('FAILED', 'BLOCKED', 'NOT_FOUND'))
            errors = sum(1 for r in self.results if r['status'] in ('TIMEOUT', 'CONN_ERROR', 'ERROR'))
            skipped = sum(1 for r in self.results if r['status'] == 'SKIPPED')

            f.write(f'Summary: {passed} passed, {rate_limited} rate-limited (endpoint works), {failed} failed, {errors} errors, {skipped} skipped\n\n')
            f.write('=' * 60 + '\n\n')

            for r in self.results:
                f.write(f'[{r["api_id"]}] {r["name"]}\n')
                f.write(f'  URL: {r["url"]}\n')
                f.write(f'  Method: {r["method"]}\n')
                f.write(f'  Status: {r["status"]} (HTTP {r["status_code"]})\n')
                f.write(f'  Time: {r["timestamp"]}\n')
                if r['error']:
                    f.write(f'  Error: {r["error"]}\n')
                f.write(f'  Response:\n')
                if isinstance(r['response_body'], dict):
                    f.write(f'    {json.dumps(r["response_body"], indent=4, ensure_ascii=False)}\n')
                else:
                    f.write(f'    {r["response_body"]}\n')
                f.write('\n')

        print(f'Results saved to {filepath}')


if __name__ == '__main__':
    tester = APITester(PHONE)
    tester.parse_api_file(API_FILE)
    tester.run_all()
    tester.save_results(RESULT_FILE)
