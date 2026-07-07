import json, urllib.request, urllib.error

BASE = "http://localhost:8000"
def call(method, path, body=None, token=None):
    req = urllib.request.Request(BASE + path, method=method,
        data=json.dumps(body).encode() if body else None,
        headers={"Content-Type": "application/json", **({"Authorization": f"Bearer {token}"} if token else {})})
    try:
        with urllib.request.urlopen(req) as r: return r.status, json.load(r)
    except urllib.error.HTTPError as e: return e.code, json.loads(e.read() or b"{}")

print("=== E2E USER JOURNEY: login -> IPC->BNS -> verification -> result ===\n")
s, r = call("POST", "/login", {"username": "analyst", "password": "nyayasetu2026"})
token = r.get("access_token", "")
print(f"1. LOGIN            -> {s} | token issued: {bool(token)} | expires_in: {r.get('expires_in')}s")
s, r = call("GET", "/me", token=token)
print(f"   whoami           -> {s} | {r}")
s, _ = call("POST", "/login", {"username": "analyst", "password": "bad"})
print(f"   wrong password   -> {s} (expected 401)")

s, r = call("GET", "/mapping?code=IPC-420")
m = r["mappings"][0]
print(f"\n2. IPC->BNS LOOKUP  -> {s} | IPC-420 -> {m['bns_code']} ({m['bns_title']}) | confidence: {m['confidence']}")
s, r = call("GET", "/search?q=cheating%20fraud")
print(f"   keyword search   -> {s} | {r['count']} hits | top: {r['results'][0]['record']['ipc_code']}")

s, r = call("GET", "/mapping/contradiction?code=IPC-420")
print(f"\n3. VERIFICATION     -> {s} | contradictions: {r['count']} | clean: {not r['has_contradictions']}")
s, r = call("GET", "/mapping/impact?section_id=IPC-420")
print(f"   impact analysis  -> {s} | total records: {r['total_records']} | chapters: {len(r['unique_chapters'])}")

s, r = call("POST", "/chat", {"question": "what replaced IPC-420 cheating?"})
print(f"\n4. RESULT (chat)    -> {s} | confidence: {r['confidence']} | cites: {[x['bns_code'] for x in r['sources']]}")
s, r = call("POST", "/agent", {"question": "verify the transition of IPC-326A acid attack"})
print(f"   agent w/ trace   -> {s} | confidence: {r['confidence']} | refs: {r['references']} | trace: {len(r['trace'])} steps")
s, r = call("POST", "/chat/summary", {"code": "IPC-304A"})
print(f"   AI summary       -> {s} | {r['summary'][:90]}")
s, r = call("POST", "/rank", {"query": "acid attack on woman", "top_k": 3})
print(f"   ML ranking       -> {s} | top: {[(x['ipc_code'], x['ml_score']) for x in r['results']]}")

s, r = call("GET", "/health")
print(f"\n5. HEALTH           -> {s} | v{r['version']} | {r['mapping_count']} mappings")
print("\n=== JOURNEY COMPLETE ===")
