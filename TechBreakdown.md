# Technical Breakdown — Interactive Proof Visualizer

This document explains how the major algorithms in the project work. It is
organized as:

1. A short tour of the UI and the data that flows through it.
2. The algorithm that decides **which inference rules can apply** to a goal.
3. A deep dive into the **automatic proof solver** (the goal-directed search
   with backtracking, memoization, and dead-end recovery).

Where helpful, the prose cites the exact functions/classes that implement
each piece so it is easy to read the code alongside this document.

---

## 1. UI Overview

The frontend is a React + TypeScript single-page app that talks to the Flask
backend over a small JSON API. It is intentionally a thin layer: the heavy
lifting (parsing, rule checking, solving) all happens in Python.

### 1.1 Component layout

The app shell is defined in `@/Users/hz/Computing/proof visulizer /frontend/src/App.tsx:336-486`.
It is organized as a vertical stack of "flow panels":

- **Header** — title strip with a "Proof Complete" chip when the proof
  closes.
- **`FormulaInput`** (`@/Users/hz/Computing/proof visulizer /frontend/src/components/FormulaInput.tsx`)
  — text box where the user types a formula in either ASCII (`A -> B`,
  `forall x. P(x)`) or Unicode (`A → B`, `∀x. P(x)`). Two buttons: **Set
  Goal** (resets the proof) and **Add Premise** (appends a hypothesis
  visible to every open goal).
- **`GoalsList`** + **`RulesPanel`** (left column,
  `@/Users/hz/Computing/proof visulizer /frontend/src/components/GoalsList.tsx`
  and `@/Users/hz/Computing/proof visulizer /frontend/src/components/RulesPanel.tsx`)
  — the list of open/proven goals on top and the rules currently applicable
  to the selected goal underneath.
- **`ProofGraph`** + **`ProofSteps`** (right column) — a Cytoscape/dagre
  rendering of the proof tree (`@/Users/hz/Computing/proof visulizer /frontend/src/components/ProofGraph.tsx`)
  and a chronological log of every rule application
  (`@/Users/hz/Computing/proof visulizer /frontend/src/components/ProofSteps.tsx`).
- **`ControlBar`** — Undo / Redo / Check / Solve / Hint / Export / Reset.

### 1.2 Data flow

After every user action `App.tsx` performs the same loop:

1. Send the action to the backend (`api.applyRule`, `api.solve`, etc.) in
   `@/Users/hz/Computing/proof visulizer /frontend/src/services/api.ts`.
2. Replace local `proofState` with the new state returned by the server.
3. Call `refreshState()` which fetches both `/api/state` (full goal/step
   serialization) and `/api/graph` (Cytoscape-ready nodes/edges produced by
   `ProofEngine.get_graph_data` at
   `@/Users/hz/Computing/proof visulizer /backend/engine/proof_engine.py:701-734`).
4. If a new goal was created, auto-select it; otherwise pick the first open
   goal so the rules panel stays useful.

### 1.3 Visual encoding

`ProofGraph.tsx` renders each `GoalNode` as a roundrectangle with three
status classes baked in at `@/Users/hz/Computing/proof visulizer /backend/engine/proof_engine.py:707-709`:

- `open` — amber border (unproven).
- `proven` — green border.
- `main` — thicker teal border on the original theorem.

Edges carry the rule name as a label (e.g. `and_intro`, `implies_intro`),
so the dagre layout reads top-down as "theorem → subgoals → closed leaves".

### 1.4 What the UI does *not* do

- It never decides whether a rule is applicable — it just shows whatever
  the `/api/list_rules` endpoint returns.
- It never builds new goals locally — every transformation is computed
  server-side and the UI just re-renders the resulting JSON.

This keeps the proof rules as the single source of truth.

---

## 2. Determining Which Rules Apply

When the user selects a goal, the UI calls `GET /api/list_rules?goal_id=…`,
which lands in `ProofEngine.list_rules` at
`@/Users/hz/Computing/proof visulizer /backend/engine/proof_engine.py:69-89`.
The endpoint returns a list of `RuleInfo` objects (name, description,
category) that the `RulesPanel` renders as buttons grouped by category.

### 2.1 The rule registry

All 24 inference rules live in `@/Users/hz/Computing/proof visulizer /backend/engine/rules.py`.
Each rule is a subclass of `InferenceRule` (`rules.py:21-39`) with two key
methods:

- `is_applicable(state, goal, params)` — pure predicate, no side effects.
- `apply(state, goal, params)` — mutates the `ProofState`, returns the IDs
  of any new subgoals.

The flat list `ALL_RULES` (`rules.py:743-773`) registers every rule and the
dictionary `RULES_BY_NAME` is used everywhere for O(1) lookup by name.

### 2.2 The applicability filter

The core entry point is `get_applicable_rules` at
`@/Users/hz/Computing/proof visulizer /backend/engine/rules.py:778-788`:

```@/Users/hz/Computing/proof visulizer /backend/engine/rules.py:778-788
def get_applicable_rules(state: ProofState, goal: GoalNode) -> List[InferenceRule]:
    """Return all rules that can be applied to the given goal."""
    if goal.is_proven:
        return []

    # If the goal formula matches an assumption, only offer 'assumption'
    assumption_strs = {str(a) for a in goal.assumptions}
    if str(goal.formula) in assumption_strs:
        return [r for r in ALL_RULES if r.name == 'assumption' and r.is_applicable(state, goal)]

    return [r for r in ALL_RULES if r.is_applicable(state, goal)]
```

Three things happen here:

1. **Proven goals get no rules.** A closed leaf is final.
2. **Assumption short-circuit.** If the goal literally matches one of the
   current assumptions, only the `assumption` rule is offered. This
   prevents the panel from suggesting `or_intro_left` on `A` when `A` is
   already a hypothesis — there is exactly one correct move and the UI
   should not invite distractions.
3. **Otherwise**, every rule whose `is_applicable` returns `True` is
   included.

### 2.3 How each rule decides applicability

The `is_applicable` predicates fall into two families:

**Goal-shape rules (introduction rules).** They inspect the *type* of
`goal.formula`. Examples:

- `AndIntro.is_applicable` (`rules.py:49-50`): `isinstance(goal.formula, And)`.
- `ImpliesIntro.is_applicable` (`rules.py:193-194`): `isinstance(goal.formula, Implies)`.
- `IntersectIntro.is_applicable` (`rules.py:522-523`):
  `isinstance(goal.formula, ElementOf) and isinstance(goal.formula.set_expr, Intersect)`.
- `ForallIntro`, `ExistsIntro`, `OrIntroLeft/Right`, `IffIntro`,
  `SubsetIntro`, `EqualityIntro`, `NotIntro`, `InductionRule` are
  structurally identical — they ask "does the goal look like X?".

**Context-driven rules (elimination rules).** They scan
`goal.assumptions` for a hypothesis they can decompose. Examples:

- `AndElimLeft/Right`: any `And` in assumptions
  (`rules.py:69-70`, `rules.py:97-98`).
- `ImpliesElim` (`rules.py:214-222`): an `A → B` assumption *plus* either a
  matching `A` assumption or a goal equal to `B` (the modus-ponens
  precondition).
- `OrElim`, `UnionElim`: any disjunction / union-membership assumption,
  but **only if both branches are not already present** so the rule would
  genuinely add information
  (see `UnionElim.is_applicable` at `rules.py:623-632`).
- `IntersectElim` similarly skips itself once both component memberships
  have already been derived (`rules.py:545-553`).
- `NotElim`: needs a `¬¬A` in assumptions where `A` equals the goal
  (`rules.py:287-291`).
- `Contradiction`: needs any `a` together with `¬a` in assumptions
  (`rules.py:349-356`).

This "look at the goal *and* look at the assumptions" pattern is what
makes the rules panel feel context-aware: the same goal under different
hypotheses produces different button lists.

### 2.4 Hiding redundant manual elims

For `union_elim` and `intersect_elim`, just checking "is there a union
assumption?" is not enough — repeatedly applying the rule to the *same*
source assumption in a single path is useless and would make the UI feel
broken. `ProofEngine` keeps a per-goal `manual_elim_history` (defined on
`GoalNode` at `@/Users/hz/Computing/proof visulizer /backend/engine/proof_state.py:13-23`),
and `list_rules` filters out elim options whose source was already
consumed:

```@/Users/hz/Computing/proof visulizer /backend/engine/proof_engine.py:79-89
        applicable = get_applicable_rules(self.state, goal)
        filtered: List[InferenceRule] = []
        for r in applicable:
            # Rules panel applies elim rules without source selection. Hide
            # options that would repeat an elim on the same source in this path.
            if self._is_manual_redundant_elim(goal, r.name):
                continue
            filtered.append(r)
```

The helpers `_is_manual_redundant_elim`, `_select_manual_elim_source`, and
`_elim_marker` (`proof_engine.py:129-176`) implement this bookkeeping:

- A marker string `"{rule_name}|{source_assumption}"` uniquely identifies
  a (rule, source) pair.
- When the user applies the rule, `_record_manual_elim_marker` writes the
  marker into the parent goal *and* every new child goal so the same
  source is never offered again on any descendant.
- Children inherit `manual_elim_history` from their parent at goal
  creation time (`proof_state.py:151-169`).

### 2.5 Putting it together

So when the panel renders for a goal `G`:

1. `list_rules(G)` is called.
2. If `G` is proven → no rules.
3. If `G.formula` matches an assumption → just `assumption`.
4. Otherwise every rule whose `is_applicable(G)` returns true is included…
5. …minus union/intersect elims that have already been used on the same
   source in this branch.

The UI then groups the result by `rule.category` (propositional,
quantifier, set_theory, induction) and color-codes the buttons
(`RulesPanel.tsx:15-21`).

---

## 3. The Proof Solver

The "Solve" button in the control bar calls `POST /api/solve`, which
invokes `ProofEngine.solve` at
`@/Users/hz/Computing/proof visulizer /backend/engine/proof_engine.py:290-324`.
The solver tries to close *all* open goals automatically. It is
fundamentally a depth-first search over rule applications with backtracking,
memoization, ancestor-cycle detection, and a recovery phase that re-runs
from scratch if the user previously committed to a dead branch.

### 3.1 Why not just brute-force DFS?

A naive "try every applicable rule on every open goal" explorer blows up
quickly because:

- Many rules are *deterministic* — there is exactly one way to apply them
  (e.g. `and_intro` must split into the two conjuncts). Trying them
  speculatively wastes time.
- Some rules *enrich* the assumption set without producing new goals (the
  `*_elim` rules). They are essentially free moves and should be done
  greedily before any branching.
- Choice rules (`or_intro_left` vs `or_intro_right`, `union_intro_left`
  vs `union_intro_right`, `or_elim`, `union_elim`) genuinely branch and
  need backtracking, but only after the cheap moves are exhausted.
- The same abstract proof state can be re-reached via different paths,
  which leads to exponential re-work without memoization.

The solver encodes all of these observations as policy.

### 3.2 The two-pass driver: `solve`

```@/Users/hz/Computing/proof visulizer /backend/engine/proof_engine.py:290-324
    def solve(self, max_steps: int = 200) -> dict:
        ...
        primary = self._attempt_solve(max_steps)
        if primary.get("is_complete"):
            return primary

        # If manual interaction committed to a dead-end branch ...
        theorem_goal = self.state.goals.get(self.state.main_goal)
        if theorem_goal is None:
            return primary

        scratch = ProofEngine()
        scratch.state.premises = copy.deepcopy(self.state.premises)
        scratch.state.set_main_goal(copy.deepcopy(theorem_goal.formula))
        recovered = scratch._attempt_solve(max_steps)
        if recovered.get("is_complete"):
            self.state = scratch.state
            ...
            return recovered

        return primary
```

The logic is:

1. **Primary pass** — try to finish from the *current* state.
2. **Recovery pass** — if that fails, build a fresh `ProofEngine` whose
   only context is the original theorem + premises, solve from scratch,
   and if it completes, swap the user's state for the scratch state.

The recovery pass is crucial because the user may have manually applied
a rule (e.g. picked `or_intro_left` when the proof actually requires the
right branch). Without recovery, the solver would be stuck in the
dead branch the user committed to.

### 3.3 The single attempt: `_attempt_solve`

```@/Users/hz/Computing/proof visulizer /backend/engine/proof_engine.py:326-357
    def _attempt_solve(self, max_steps: int = 200) -> dict:
        self.state.save_checkpoint()
        self._solve_steps = 0
        self._solve_max = max_steps
        self._state_depth_seen: Dict[tuple, int] = {}
        self._failed_goal_depth: Dict[str, int] = {}

        snapshot = self.state._snapshot()
        search_depth = max(1, max_steps)
        if self._solve_all_goals(search_depth):
            return { "success": True, "is_complete": True, ... }

        self.state._restore(snapshot)
        return { "success": True, "is_complete": False, ... }
```

Key bookkeeping created at the start of every attempt:

- `_solve_steps` / `_solve_max` — hard cap on rule applications, so a
  pathological search cannot hang the server.
- `_state_depth_seen` — maps an abstract *frontier signature* (defined
  below) to the deepest depth at which it was explored. If the same
  frontier reappears at the same or shallower remaining depth, the
  recursion is cut off.
- `_failed_goal_depth` — maps individual goal signatures to the max
  depth at which they have already failed.
- `snapshot` — a checkpoint of the full state used to roll back on
  failure so the user's view is unchanged after a failed solve.

### 3.4 The all-goals scheduler: `_solve_all_goals`

```@/Users/hz/Computing/proof visulizer /backend/engine/proof_engine.py:359-381
    def _solve_all_goals(self, depth: int) -> bool:
        if self.state.is_complete():
            return True
        if depth <= 0 or self._solve_steps >= self._solve_max:
            return False
        ...
        state_sig = self._state_sig()
        seen_depth = self._state_depth_seen.get(state_sig, -1)
        if seen_depth >= depth:
            return False
        self._state_depth_seen[state_sig] = depth

        open_goals.sort(key=self._goal_priority)
        goal_id = open_goals[0].id
        return self._solve_goal(goal_id, depth)
```

Two ideas:

- **Frontier memoization.** `_state_sig` (`proof_engine.py:630-632`)
  returns the sorted tuple of every open goal's signature. If we have
  already explored this exact frontier with at least as much remaining
  depth, we will not get a better outcome by trying again, so we prune.
- **Goal selection heuristic.** `_goal_priority`
  (`proof_engine.py:647-662`) sorts open goals by:
  1. Whether they close immediately by `assumption`.
  2. Whether they have a deterministic structural rule.
  3. Size of the assumption set (smaller first).
  4. Goal ID as a tie-breaker for determinism.

  We always work on the highest-priority goal first, so "obviously
  closable" subgoals never block on "needs a hard case split" subgoals.

### 3.5 The per-goal driver: `_solve_goal`

```@/Users/hz/Computing/proof visulizer /backend/engine/proof_engine.py:383-407
    def _solve_goal(self, goal_id: str, depth: int) -> bool:
        ...
        sig = self._goal_sig(goal)
        seen_fail_depth = self._failed_goal_depth.get(sig, -1)
        if seen_fail_depth >= depth:
            return False

        if self._repeats_ancestor_state(goal):
            return False

        solved = self._try_solve_goal(goal_id, goal, depth)
        if not solved:
            prev = self._failed_goal_depth.get(sig, -1)
            if depth > prev:
                self._failed_goal_depth[sig] = depth
        return solved
```

Two anti-loop mechanisms here:

- **Goal-level failure memoization.** If a goal with signature `S`
  already failed at depth `D`, it will fail again at any depth `≤ D`.
- **Ancestor cycle detection.** `_repeats_ancestor_state`
  (`proof_engine.py:634-645`) walks up the goal's parent chain. If any
  ancestor has the exact same `(formula, assumptions)` signature, we are
  trapped in a local cycle (typical when alternating `intro`/`elim` on
  the same connective) and the branch is abandoned.

### 3.6 The strategy core: `_try_solve_goal`

This is where domain knowledge about natural deduction lives. The
docstring at `proof_engine.py:409-419` lays out the four phases:

```@/Users/hz/Computing/proof visulizer /backend/engine/proof_engine.py:409-419
    def _try_solve_goal(self, goal_id: str, goal, depth: int) -> bool:
        """Core goal-directed solving logic.

        Strategy:
        1. Close immediately if possible (assumption, contradiction)
        2. For deterministic intro rules (and_intro, implies_intro, etc.),
           apply them directly — they have exactly one decomposition.
        3. For goals needing enrichment, apply ONE elim rule at a time,
           then recurse (which re-checks assumption and structural rules).
        4. For choice rules, try each option with backtracking.
        """
```

**Phase 1 — Immediate close.**

```@/Users/hz/Computing/proof visulizer /backend/engine/proof_engine.py:420-429
        f = goal.formula
        assumption_strs = set(str(a) for a in goal.assumptions)

        if str(f) in assumption_strs:
            return self._try_rule('assumption', goal_id, depth)

        if isinstance(f, Bottom):
            if self._try_rule('contradiction', goal_id, depth):
                return True
```

If the goal text matches a hypothesis, close with `assumption`. If the
goal is `⊥`, try to derive a contradiction directly from the current
assumptions.

**Phase 2 — Deterministic structural rules.** `_structural_rules`
(`proof_engine.py:473-520`) inspects the goal's top-level connective and
returns the matching introduction rule(s). A goal of the form `A ∧ B`
gets `and_intro`, `A → B` gets `implies_intro`, `∀x.P(x)` gets
`forall_intro`, `x ∈ A ∩ B` gets `intersect_intro`, and so on.

For *deterministic* rules (only one way to decompose) the solver fires
them immediately:

```@/Users/hz/Computing/proof visulizer /backend/engine/proof_engine.py:434-441
        deterministic = {'and_intro', 'implies_intro', 'not_intro', 'iff_intro',
                         'forall_intro', 'exists_intro', 'equality_intro',
                         'subset_intro', 'intersect_intro'}

        for rule_name in structural:
            if rule_name in deterministic:
                return self._try_rule(rule_name, goal_id, depth)
```

Crucially, this returns the result of `_try_rule` directly — the
deterministic rule is the *only* sensible move, so its success/failure
determines the branch's outcome.

**Phase 3 — Non-branching elimination ("free enrichment").**

```@/Users/hz/Computing/proof visulizer /backend/engine/proof_engine.py:446-451
        elim_rules = self._useful_elim_rules(goal)
        non_branching = [r for r in elim_rules if r not in ('union_elim', 'or_elim')]
        for rule_name in non_branching:
            if self._try_rule(rule_name, goal_id, depth):
                return True
```

`_useful_elim_rules` (`proof_engine.py:522-568`) scans the assumptions
and returns only the elim rules that would actually produce new
information — for instance, `and_elim_left` is only offered if `A ∧ B`
is in scope and `A` is *not* already an assumption. `implies_elim` is
offered when both the antecedent and the implication are in scope but
the consequent is not. This avoids "applying" rules that add duplicates.

Non-branching elims (`and_elim_left`, `and_elim_right`, `intersect_elim`,
`implies_elim`, `contradiction`) add facts to the same goal's assumption
list without spawning new goals, so they are cheap to try.

**Phase 4 — Branching choice rules.** Disjunctive goals
(`A ∨ B`, `x ∈ A ∪ B`) and case splits (`or_elim`, `union_elim`) are
inherently branching. The solver has a special policy here: sometimes
it is smarter to *case-split first* than to commit to one disjunct.

```@/Users/hz/Computing/proof visulizer /backend/engine/proof_engine.py:452-469
        branching = [r for r in elim_rules if r in ('union_elim', 'or_elim')]

        if self._prefer_branching_before_intro(goal, structural, assumption_strs):
            for rule_name in branching:
                if self._try_rule(rule_name, goal_id, depth):
                    return True

        # Phase 4: Try structural choice rules (union_intro, or_intro)
        for rule_name in structural:
            if self._try_rule(rule_name, goal_id, depth):
                return True

        # Phase 5: Try branching elim rules (union_elim, or_elim) as fallback
        for rule_name in branching:
            if self._try_rule(rule_name, goal_id, depth):
                return True
```

`_prefer_branching_before_intro` (`proof_engine.py:664-682`) returns
`True` when the goal is `A ∨ B` (or `x ∈ A ∪ B`) and *neither* disjunct
is currently a hypothesis. In that situation, committing to one intro
branch is a gamble; doing the elim case split first usually yields one
case that closes immediately.

The order of fallbacks — choice intros first, then branching elims — is
the standard heuristic: try to *prove* the goal before *destroying*
hypotheses.

### 3.7 Trying a rule with backtracking: `_try_rule`

```@/Users/hz/Computing/proof visulizer /backend/engine/proof_engine.py:587-620
    def _try_rule(self, rule_name: str, goal_id: str, depth: int,
                  params: Dict = None) -> bool:
        ...
        snapshot = self.state._snapshot()
        old_steps = self._solve_steps

        try:
            goal = self.state.goals[goal_id]
            rule.apply(self.state, goal, params)
            self._dedupe_all_goal_assumptions()
            self._solve_steps += 1

            if self._solve_all_goals(depth - 1):
                return True

            self.state._restore(snapshot)
            self._solve_steps = old_steps
            return False
        except Exception:
            self.state._restore(snapshot)
            self._solve_steps = old_steps
            return False
```

This is the textbook backtracking pattern:

1. Snapshot the entire `ProofState`
   (`@/Users/hz/Computing/proof visulizer /backend/engine/proof_state.py:80-100`).
2. Apply the rule. If the rule raises `RuleError` (or anything else),
   roll back and report failure.
3. Recurse into `_solve_all_goals` with `depth - 1`.
4. On success, leave the new state in place. On failure, restore the
   snapshot and the step counter so other branches start from the same
   baseline.

### 3.8 Signatures and dedupe

A few small helpers tie everything together:

- `_goal_sig` / `_goal_sig_parts` (`proof_engine.py:622-628`) — turns a
  goal into a string of the form `"<formula>||(<sorted assumptions>)"`.
  Two goals with the same signature are considered equivalent for
  memoization purposes.
- `_state_sig` (`proof_engine.py:630-632`) — sorted tuple of all open
  goal signatures.
- `_dedupe_all_goal_assumptions` (`proof_engine.py:684-687`) — calls
  `ProofState.dedupe_assumptions` on every goal after each rule
  application. This is what lets `_useful_elim_rules` rely on string
  comparison to detect duplicates: `[A ∧ B, A, A]` is normalized to
  `[A ∧ B, A]` immediately.

### 3.9 End-to-end example

Consider the theorem `A ∩ (B ∪ C) = (A ∩ B) ∪ (A ∩ C)`.

1. `set_goal` parses the formula and stores it as the main goal `G1`.
2. The user clicks **Solve**. `solve` → `_attempt_solve` →
   `_solve_all_goals`.
3. `_solve_goal(G1)` calls `_try_solve_goal`. The goal is `Equals(...)`
   so `_structural_rules` returns `['equality_intro']`, which is in the
   `deterministic` set → `equality_intro` fires, producing two subgoals
   `G2: A ∩ (B ∪ C) ⊆ (A ∩ B) ∪ (A ∩ C)` and `G3: …`.
4. Each `Subset` subgoal triggers `subset_intro` (deterministic), which
   introduces a fresh `x ∈ A ∩ (B ∪ C)` assumption and asks to prove
   `x ∈ (A ∩ B) ∪ (A ∩ C)`.
5. The resulting goal is a Union membership. `_prefer_branching_before_intro`
   detects that neither `x ∈ A ∩ B` nor `x ∈ A ∩ C` is in assumptions, so
   the solver runs `intersect_elim` (non-branching enrichment, phase 3),
   adding `x ∈ A` and `x ∈ B ∪ C` to the context, then `union_elim` on
   `x ∈ B ∪ C` (phase 5 fallback) to case-split.
6. In each case the structural `union_intro_left` / `union_intro_right`
   plus `intersect_intro` plus `assumption` closes the goal.
7. When all goals close, `_solve_all_goals` returns `True`, the state is
   left committed, and the API responds with `is_complete: true` and the
   step count.

Throughout this trace, the memoization tables ensure that any branch
that revisits an equivalent `(open goals, depth)` pair returns `False`
immediately rather than re-exploring, and the ancestor-cycle check kills
any pathological loop introduced by, say, repeatedly `or_elim`-ing the
same disjunct.

---

## 4. Where to read next

- Rule semantics: `@/Users/hz/Computing/proof visulizer /backend/engine/rules.py`.
- State + history + serialization: `@/Users/hz/Computing/proof visulizer /backend/engine/proof_state.py`.
- Parser grammar: `@/Users/hz/Computing/proof visulizer /backend/parser/formula_parser.py:30-110`.
- Z3 hint integration (optional validity check used by
  `get_hint_with_solver`):
  `@/Users/hz/Computing/proof visulizer /backend/solvers/z3_solver.py`.
- Frontend entry point and layout:
  `@/Users/hz/Computing/proof visulizer /frontend/src/App.tsx`.
