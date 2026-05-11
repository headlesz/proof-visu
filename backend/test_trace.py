import sys, signal
sys.path.insert(0, ".")
signal.signal(signal.SIGALRM, lambda s, f: (log.close(), sys.exit(1)))
signal.alarm(8)

from engine.proof_engine import ProofEngine

log = open("trace.log", "w")
C = [0]
orig = ProofEngine._try_solve_goal
def t(self, gid, goal, depth):
    C[0] += 1
    f = str(goal.formula)[:60]
    sr = self._structural_rules(goal.formula, goal)
    er = self._useful_elim_rules(goal)
    det = {'and_intro','implies_intro','not_intro','iff_intro',
           'forall_intro','exists_intro','equality_intro',
           'subset_intro','intersect_intro'}
    tag = 'DET' if any(r in det for r in sr) else ('CHC' if sr else 'ELM')
    log.write(f"{C[0]:4d} {gid:5s} d={depth:2d} [{tag}] {f}\n")
    log.write(f"     sr={sr} er={er}\n")
    if C[0] % 100 == 0:
        log.flush()
    return orig(self, gid, goal, depth)
ProofEngine._try_solve_goal = t

e = ProofEngine()
e.set_goal("A union (B cap C) = (A union B) cap (A union C)")
r = e.solve(200)
log.write(f"\ncalls={C[0]} done={r['is_complete']} steps={r['steps_taken']}\n")
log.close()
print(f"calls={C[0]} done={r['is_complete']}")
