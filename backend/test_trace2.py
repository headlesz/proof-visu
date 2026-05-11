import sys
sys.path.insert(0, ".")
from engine.proof_engine import ProofEngine

e = ProofEngine()
e.set_goal("A union (B cap C) = (A union B) cap (A union C)")

# Trace the solver
C = [0]
orig = ProofEngine._try_solve_goal
def traced(self, gid, goal, depth):
    C[0] += 1
    f = str(goal.formula)[:55]
    assump = [str(a)[:30] for a in goal.assumptions]
    sr = self._structural_rules(goal.formula, goal)
    er = self._useful_elim_rules(goal)
    print(f"{C[0]:3d} {gid:5s} d={depth:2d} {f}")
    print(f"      assump={assump} sr={sr} er={er}")
    if C[0] > 150:
        print("STOPPING TRACE")
        return False
    return orig(self, gid, goal, depth)
ProofEngine._try_solve_goal = traced

r = e.solve(200)
print(f"\ncalls={C[0]} done={r['is_complete']} steps={r['steps_taken']}")
print(r["message"])
