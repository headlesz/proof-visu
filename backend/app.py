"""
Flask backend for the Interactive Proof Visualizer.
Provides REST API endpoints for proof construction, rule application, hints, and export.
"""
import sys
import os
import logging
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

sys.path.insert(0, os.path.dirname(__file__))

from engine.proof_engine import ProofEngine

app = Flask(__name__, static_folder='../frontend/build', static_url_path='')
CORS(app)

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# Store engines per session (simple in-memory; production would use sessions/DB)
engines = {}


def get_engine(session_id: str = "default") -> ProofEngine:
    """Get or create a proof engine for the given session."""
    if session_id not in engines:
        engines[session_id] = ProofEngine()
    return engines[session_id]


@app.route('/')
def serve_frontend():
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "ok", "message": "Proof Visualizer API is running"})


@app.route('/api/parse', methods=['POST'])
def parse_formula():
    """Parse a formula string; return success or syntax error."""
    data = request.get_json()
    formula_str = data.get('formula', '')
    session_id = data.get('session_id', 'default')

    if not formula_str:
        return jsonify({"success": False, "error": "No formula provided"}), 400

    engine = get_engine(session_id)
    result = engine.parse_formula(formula_str)
    logger.info(f"Parse '{formula_str}': {'ok' if result['success'] else result.get('error')}")
    return jsonify(result)


@app.route('/api/new_goal', methods=['POST'])
def new_goal():
    """Set the main goal; initializes proof state."""
    data = request.get_json()
    formula_str = data.get('formula', '')
    session_id = data.get('session_id', 'default')

    if not formula_str:
        return jsonify({"success": False, "error": "No formula provided"}), 400

    engine = get_engine(session_id)
    result = engine.set_goal(formula_str)
    logger.info(f"New goal '{formula_str}': {'ok' if result['success'] else result.get('error')}")
    return jsonify(result)


@app.route('/api/add_premise', methods=['POST'])
def add_premise():
    """Add a premise to context."""
    data = request.get_json()
    formula_str = data.get('formula', '')
    session_id = data.get('session_id', 'default')

    if not formula_str:
        return jsonify({"success": False, "error": "No formula provided"}), 400

    engine = get_engine(session_id)
    result = engine.add_premise(formula_str)
    logger.info(f"Add premise '{formula_str}': {'ok' if result['success'] else result.get('error')}")
    return jsonify(result)


@app.route('/api/remove_premise', methods=['POST'])
def remove_premise():
    """Remove a premise from context by index."""
    data = request.get_json() or {}
    session_id = data.get('session_id', 'default')
    premise_index = data.get('premise_index', None)

    if premise_index is None:
        return jsonify({"success": False, "error": "premise_index is required"}), 400

    try:
        premise_index = int(premise_index)
    except (TypeError, ValueError):
        return jsonify({"success": False, "error": "premise_index must be an integer"}), 400

    engine = get_engine(session_id)
    result = engine.remove_premise(premise_index)
    logger.info(
        f"Remove premise {premise_index}: "
        f"{'ok' if result['success'] else result.get('error')}"
    )
    return jsonify(result)


@app.route('/api/list_rules', methods=['GET'])
def list_rules():
    """List applicable rules for a given goal."""
    goal_id = request.args.get('goal_id', '')
    session_id = request.args.get('session_id', 'default')

    if not goal_id:
        return jsonify({"success": False, "error": "No goal_id provided"}), 400

    engine = get_engine(session_id)
    result = engine.list_rules(goal_id)
    return jsonify(result)


@app.route('/api/apply_rule', methods=['POST'])
def apply_rule():
    """Apply a specific rule to a goal."""
    data = request.get_json()
    goal_id = data.get('goal_id', '')
    rule_name = data.get('rule', '')
    params = data.get('params', {})
    session_id = data.get('session_id', 'default')

    if not goal_id or not rule_name:
        return jsonify({"success": False, "error": "goal_id and rule are required"}), 400

    engine = get_engine(session_id)
    result = engine.apply_rule(goal_id, rule_name, params)
    logger.info(f"Apply {rule_name} to {goal_id}: {'ok' if result['success'] else result.get('error')}")
    return jsonify(result)


@app.route('/api/undo', methods=['POST'])
def undo():
    """Undo last action."""
    data = request.get_json() or {}
    session_id = data.get('session_id', 'default')
    engine = get_engine(session_id)
    result = engine.undo()
    return jsonify(result)


@app.route('/api/redo', methods=['POST'])
def redo():
    """Redo last undone action."""
    data = request.get_json() or {}
    session_id = data.get('session_id', 'default')
    engine = get_engine(session_id)
    result = engine.redo()
    return jsonify(result)


@app.route('/api/hint', methods=['GET'])
def hint():
    """Get a hint for a given goal."""
    goal_id = request.args.get('goal_id', '')
    session_id = request.args.get('session_id', 'default')
    use_solver = request.args.get('use_solver', 'false').lower() == 'true'

    if not goal_id:
        return jsonify({"success": False, "error": "No goal_id provided"}), 400

    engine = get_engine(session_id)
    if use_solver:
        result = engine.get_hint_with_solver(goal_id)
    else:
        result = engine.get_hint(goal_id)
    return jsonify(result)


@app.route('/api/check', methods=['GET'])
def check_proof():
    """Check if proof is complete."""
    session_id = request.args.get('session_id', 'default')
    engine = get_engine(session_id)
    result = engine.check_proof()
    return jsonify(result)


@app.route('/api/solve', methods=['POST'])
def solve_proof():
    """Automatically solve the current proof."""
    data = request.get_json() or {}
    session_id = data.get('session_id', 'default')
    max_steps = data.get('max_steps', 200)
    engine = get_engine(session_id)
    result = engine.solve(max_steps)
    logger.info(f"Solve: {result.get('message')}")
    return jsonify(result)


@app.route('/api/state', methods=['GET'])
def get_state():
    """Get current proof state."""
    session_id = request.args.get('session_id', 'default')
    engine = get_engine(session_id)
    return jsonify(engine.get_state())


@app.route('/api/graph', methods=['GET'])
def get_graph():
    """Get proof graph data for visualization."""
    session_id = request.args.get('session_id', 'default')
    engine = get_engine(session_id)
    return jsonify(engine.get_graph_data())


@app.route('/api/export', methods=['GET'])
def export_proof():
    """Export current proof as JSON or LaTeX."""
    session_id = request.args.get('session_id', 'default')
    fmt = request.args.get('format', 'json')
    engine = get_engine(session_id)

    if fmt == 'latex':
        latex = engine.export_latex()
        return jsonify({"success": True, "format": "latex", "content": latex})
    else:
        data = engine.export_json()
        return jsonify({"success": True, "format": "json", "content": data})


@app.route('/api/reset', methods=['POST'])
def reset():
    """Reset the proof session."""
    data = request.get_json() or {}
    session_id = data.get('session_id', 'default')
    engines[session_id] = ProofEngine()
    return jsonify({"success": True, "message": "Session reset"})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)
