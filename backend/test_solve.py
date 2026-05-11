import sys, time, signal
sys.path.insert(0, ".")

def timeout_handler(sig, frame):
    print("TIMEOUT")
    sys.exit(1)

signal.signal(signal.SIGALRM, timeout_handler)

from engine.proof_engine import ProofEngine

tests = [
    ("identity", "p -> p"),
    ("commut", "(p && q) -> (q && p)"),
    ("contra", "(p -> q) -> (~q -> ~p)"),
    ("simp", "(p && q) -> p"),
    ("set_eq", "A = A"),
    ("distrib", "A union (B cap C) = (A union B) cap (A union C)"),
]

for name, formula in tests:
    signal.alarm(30)
    e = ProofEngine()
    e.set_goal(formula)
    t0 = time.time()
    r = e.solve(200)
    t = time.time() - t0
    status = "OK" if r["is_complete"] else "FAIL"
    print(f"{name:12s} [{status}] steps={r['steps_taken']:3d} t={t:.2f}s | {r['message']}")

signal.alarm(0)
print("All tests done.")
