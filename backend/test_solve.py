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
    ("impl_or", "p -> q <-> ~p or q"),
    ("simp", "(p && q) -> p"),
    ("set_eq", "A = A"),
    ("distrib_fwd", "(A union (B cap C)) subset ((A union B) cap (A union C))"),
    ("distrib_rev", "((A union B) cap (A union C)) subset (A union (B cap C))"),
    ("distrib", "A union (B cap C) = (A union B) cap (A union C)"),
    ("comp_empty", "A cap Aᶜ = emptyset"),
    ("demorgan_union", "(A union B)ᶜ = (Aᶜ cap Bᶜ)"),
    ("demorgan_inter", "(A cap B)ᶜ = (Aᶜ union Bᶜ)"),
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

e_latex = ProofEngine()
e_latex.set_goal("p -> q <-> ~p or q")
r_latex = e_latex.solve(200)
assert r_latex["is_complete"], "latex regression theorem should solve"
latex = e_latex.export_latex()
assert "By biconditional introduction, it suffices to prove both" in latex
assert "By excluded middle, split into the cases $p$ and its negation." in latex
assert "By modus ponens, derive $q$." in latex
assert "By disjunction elimination on $(\\neg p \\lor q)$, prove the goal in each case." in latex
assert latex.find("\\textbf{Forward direction:}") < latex.find("\\textbf{Backward direction:}")
assert "\\begin<class" not in latex
print("latex_export [OK] structured biconditional proof export")

e_premise = ProofEngine()
assert e_premise.add_premise("p")["success"]
assert e_premise.set_goal("q")["success"]
state_with_premise = e_premise.get_state()
assert state_with_premise["premises"] == ["p"]
assert "p" in state_with_premise["goals"]["G1"]["assumptions"]
removed = e_premise.remove_premise(0)
assert removed["success"], removed
state_without_premise = removed["state"]
assert state_without_premise["premises"] == []
assert "p" not in state_without_premise["goals"]["G1"]["assumptions"]
print("remove_premise [OK] premise removed from context")

e_chain = ProofEngine()
assert e_chain.add_premise("p -> q")["success"]
assert e_chain.add_premise("~r -> ~q")["success"]
assert e_chain.add_premise("~r")["success"]
assert e_chain.set_goal("~p")["success"]
r_chain = e_chain.solve(200)
assert r_chain["is_complete"], r_chain
print("premise_chain [OK] derived ~p from manual premises")

e_goal_chain = ProofEngine()
assert e_goal_chain.add_premise("p → q")["success"]
assert e_goal_chain.add_premise("¬r → ¬q")["success"]
assert e_goal_chain.set_goal("¬r ⇒ ¬p")["success"]
r_goal_chain = e_goal_chain.solve(200)
assert r_goal_chain["is_complete"], r_goal_chain
print("unicode_implies_chain [OK] parsed ⇒ and proved implication")

# UI regression: if user manually takes a bad branch mid-proof, solve() should
# still recover by re-solving from the theorem.
e = ProofEngine()
e.set_goal("A union (B cap C) = (A union B) cap (A union C)")
manual_prefix = [
    ("G1", "equality_intro"),
    ("G2", "subset_intro"),
    ("G4", "intersect_intro"),
    ("G5", "union_intro_left"),  # commits to the wrong branch for this subgoal
]
for gid, rule in manual_prefix:
    rr = e.apply_rule(gid, rule)
    assert rr["success"], f"manual prefix failed at {gid}:{rule} => {rr}"

signal.alarm(30)
t0 = time.time()
r = e.solve(200)
t = time.time() - t0
status = "OK" if r["is_complete"] else "FAIL"
print(f"manual_recover [{status}] steps={r['steps_taken']:3d} t={t:.2f}s | {r['message']}")
assert r["is_complete"], "manual dead-end recovery solve should complete"

# UI regression: repeated elim on the same source should be filtered from rules
# to avoid manual proof-tree duplication loops.
e2 = ProofEngine()
e2.set_goal("((A union B) cap (A union C)) subset (A union (B cap C))")
assert e2.apply_rule("G1", "subset_intro")["success"]
assert e2.apply_rule("G2", "intersect_elim")["success"]
assert e2.apply_rule("G2", "union_elim")["success"]

rules_g4 = e2.list_rules("G4")
assert rules_g4["success"], f"list_rules failed: {rules_g4}"
rule_names_g4 = [x["name"] for x in rules_g4["rules"]]
assert "intersect_elim" not in rule_names_g4, (
    "intersect_elim should be hidden after being used on the same source along this path"
)
print("manual_elim_guard [OK] intersect_elim correctly filtered on repeated source")
