# Interactive Proof Visualizer

A web-based interactive proof visualizer for discrete mathematics education. Build formal proofs step-by-step with visual feedback, automated hints, and support for propositional logic, predicate logic, set theory, and induction.

## Features

- **Interactive Proof Construction**: Point-and-click interface for building proofs
- **Visual Feedback**: Dynamic proof tree/graph visualization
- **Automated Hints**: Z3 SMT solver and Prover9 integration for suggestions
- **Multiple Logics**: Propositional, first-order predicate logic, set theory, and induction
- **Undo/Redo**: Full history tracking for exploration
- **Export**: Save proofs as JSON or LaTeX

## Tech Stack

**Backend:**
- Python 3.8+
- Flask
- Lark (parser)
- Z3-solver (SMT)
- SymPy (logic)

**Frontend:**
- React with TypeScript
- Cytoscape.js (graph visualization)
- Material-UI (components)
- MathJax (formula rendering)

## Installation

### Backend Setup

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Frontend Setup

```bash
cd frontend
npm install
```

## Running the Application

You need **two terminals** — one for the backend and one for the frontend.

### Starting the Backend (Terminal 1)

```bash
cd backend
source venv/bin/activate
python app.py
```

The backend API will start on `http://localhost:5001`.

### Starting the Frontend (Terminal 2)

```bash
cd frontend
npm start
```

The React dev server will start on `http://localhost:3000` and proxy API requests to the backend.

### Stopping the Application

- **Backend:** Press `Ctrl+C` in Terminal 1.
- **Frontend:** Press `Ctrl+C` in Terminal 2.

Both processes must be stopped independently.

## Usage

1. Enter a goal formula (e.g., `A ∩ (B ∪ C) = (A ∩ B) ∪ (A ∩ C)`)
2. Click "Set Goal" to initialize the proof
3. Select a goal from the goals list
4. Choose an applicable inference rule from the actions panel
5. Continue applying rules until all goals are proven
6. Use "Hint" for automated suggestions
7. Export your completed proof

## Project Structure

```
proof-visualizer/
├── backend/
│   ├── app.py              # Flask application
│   ├── parser/             # Formula parser
│   ├── engine/             # Proof inference engine
│   ├── solvers/            # Z3 and Prover9 integration
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/     # React components
│   │   ├── services/       # API services
│   │   └── App.tsx
│   └── package.json
└── README.md
```

## License

MIT License
