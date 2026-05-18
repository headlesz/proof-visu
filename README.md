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

## Production Deployment

A turnkey `deploy.sh` script is included at the repo root. It provisions a
single Linux host (tested on Ubuntu 22.04 / Debian 12) end-to-end:

1. Installs OS-level prerequisites — Python 3 + venv, Node.js 18 (via
   NodeSource), and nginx.
2. Creates `backend/venv`, installs `backend/requirements.txt`, and adds
   `gunicorn` as the production WSGI server.
3. Runs `npm ci` and `npm run build` in `frontend/`, producing a static
   bundle at `frontend/build/`.
4. Generates `deploy/nginx.proof-visualizer.conf` — an nginx reverse proxy
   that serves the React build from `/` and forwards `/api/*` to gunicorn
   on `127.0.0.1:5001`. Includes gzip, long-cache for `/static/`, basic
   security headers, and a SPA fallback to `index.html`.
5. Generates `deploy/proof-visualizer.service` — a systemd unit that runs
   `gunicorn app:app` against the Flask backend.
6. On Linux with sudo, installs the nginx site to
   `/etc/nginx/sites-available/`, symlinks it into `sites-enabled/`,
   reloads nginx, and starts the systemd service.

### Usage

```bash
# Full deploy with a real hostname
sudo APP_DOMAIN=proofs.example.com ./deploy.sh

# Catch-all (any Host header) — useful for raw-IP access
sudo ./deploy.sh

# Build only (no apt / systemd / nginx mutations); safe locally
./deploy.sh --no-system
```

### Configuration

Override via environment variables before invoking the script:

| Variable           | Default | Purpose                                |
|--------------------|---------|----------------------------------------|
| `APP_DOMAIN`       | `_`     | nginx `server_name`                    |
| `BACKEND_PORT`     | `5001`  | Port gunicorn binds on `127.0.0.1`     |
| `GUNICORN_WORKERS` | `2`     | Number of gunicorn worker processes    |

### Reverse proxy layout

```
                 ┌──────────────────────────────┐
  Browser  ──►   │  nginx  (port 80)            │
                 │   /         → frontend/build │
                 │   /api/*    → 127.0.0.1:5001 │
                 └──────────────┬───────────────┘
                                │
                                ▼
                 ┌──────────────────────────────┐
                 │  gunicorn  (systemd)         │
                 │   app:app  (Flask backend)   │
                 └──────────────────────────────┘
```

### Heads-up about session state

The Flask backend keeps per-session proof state in an in-memory dictionary
(`backend/app.py`, `engines = {}`). With `GUNICORN_WORKERS > 1`, two
requests for the same session may land on different workers and see
divergent state. For now keep `GUNICORN_WORKERS=1`, or refactor the
session store to something shared (e.g. Redis) before scaling up.

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
├── deploy/                 # Generated nginx + systemd configs (created by deploy.sh)
├── deploy.sh               # One-shot production deploy script
├── TechBreakdown.md        # Algorithm-level technical writeup
└── README.md
```

## License

MIT License
