### School Election App - Developer Documentation

This document provides a developer-focused overview of the School Election App, including architecture, key modules, configuration, endpoints, build/run workflow, and improvement opportunities.


## 1) Architecture Overview

- **Stack**
  - **Backend**: FastAPI (`fastapi`, `uvicorn`)
  - **Templating**: Jinja2 (`jinja2`)
  - **Static/UI**: Bootstrap (bundled CSS/JS under `static/`)
  - **Persistence**: Excel file (`openpyxl` writes to `votes.xlsx`)
  - **Packaging**: PyInstaller (`.spec` and CLI)
  - **Utilities**: `itsdangerous` for lightweight cookie session data, `filelock` for process/file locking, `Pillow` for image ops, `matplotlib` + `reportlab` for export

- **Runtime Layout**
  - Templates and baked app code live under the application path. When bundled with PyInstaller, `APPLICATION_PATH` points to the internal bundle and `EXTERNAL_FILES_PATH` points to the folder containing the executable.
  - External, user-editable assets (settings, images, votes) live alongside the executable:
    - `settings/config.json` and `settings/candidates.json`
    - `static/images/...` (including `candidates/`)
    - `votes.xlsx` (created on first run)

- **Session model**
  - A per-process random `SECRET_KEY` is generated at startup and used by `itsdangerous.URLSafeSerializer` to sign a simple cookie named `session`.
  - Cookie contains either `{is_admin: True}` (admin session) or `{is_student: True, voted_posts: [...]}` (student session tracking posts already voted in this session).

- **Single-instance enforcement**
  - A lock file in the OS temp directory, uniquely derived from the app path, prevents concurrent instances. If a lock exists, the app tries to signal the existing instance at `/internal-shutdown` and retries a few times before failing.


## 2) Key Modules and Files

- `main.py`
  - App initialization, static mount, template binding
  - Config/candidates loading and default generation
  - Vote storage to `votes.xlsx` with `filelock` and retry logic
  - Routes for student flow, admin login, results, exports, and shutdown
  - Single-instance lock + automatic browser open + server lifecycle

- `settings/config.json`
  - Branding (school name, logo, background), theme, admin username/password

- `settings/candidates.json`
  - Map of post -> list of candidate names (displayed as-is)

- `templates/*.html`
  - `base.html`: Core layout, navbar controls for student/admin states, background handling
  - `index.html`: Entry page with Admin / Student flows
  - `posts.html`: Lists available posts, marks already-voted posts (via session cookie)
  - `vote.html`: Candidate selection grid with images
  - `results.html`: Aggregated results with percentages and export buttons
  - `admin_login.html`, `error.html`, `thankyou.html` (supporting pages)

- `static/`
  - `css/bootstrap.min.css`
  - `js/bootstrap.bundle.min.js`
  - `images/` including `candidates/`, defaults like `contact.png`, branding assets

- `votes.xlsx`
  - Created automatically with headers `Timestamp | Post | CandidateName`; append-only writes with basic cleanup


## 3) Configuration

- Location: `settings/config.json`
- Shape:
  ```json
  {
    "school_name": "Your School Name",
    "logo_url": "/static/images/school_logo.svg",
    "background_url": "/static/images/school_bg.jpg",
    "admin_username": "admin",
    "admin_password": "admin123",
    "theme_name": "primary",
    "available_themes": ["primary","secondary","light","warning","info"]
  }
  ```
- Notes:
  - If `config.json` is missing/invalid, a sane default is generated.
  - `theme_name` adjusts certain navbar/button color behaviors in `base.html`.
  - `background_url` can be an internal static path; a default is generated if missing.

- Candidates: `settings/candidates.json`
  - Example:
    ```json
    {
      "School Pupil Leader (Boys)": ["Candidate A", "Candidate B"],
      "School Pupil Leader (Girls)": ["Candidate C"]
    }
    ```
  - If missing, the app will create a file with two default empty posts.


## 4) Endpoints

- `GET /` — Landing page; choose Admin or Student
- `GET /admin-login` — Admin login page
- `POST /admin-login` — Form submit; sets `{is_admin: True}` cookie on success
- `GET /student-voting` — Starts a new student session with empty `voted_posts`, then redirects to `/posts`
- `GET /posts` — Lists posts; requires `{is_student: True}`; redirects admins to `/results`
- `GET /vote/{post}` — Candidate selection page for a given post; requires student session
- `POST /vote/{post}` — Records a vote, updates `voted_posts` in cookie, and redirects to `/posts`
- `GET /reset-voting` — Clears `voted_posts` but keeps student mode; returns to `/posts`
- `GET /end-voting` — Ends student session and returns to `/`
- `GET /results` — Admin-only; displays results with percentages
- `GET /export-results-image` — Exports results table to `school_election_results.png`
- `GET /export-results-pdf` — Exports results table to `school_election_results.pdf` (matplotlib PDF)
- `GET /export-results-reportlab` — Exports results table to `results_table.pdf` (reportlab)
- `GET /shutdown` — Admin-only; signals uvicorn to exit
- `GET /internal-shutdown` — Localhost-only; used during single-instance negotiation


## 5) Data and Concurrency

- Votes are appended to `votes.xlsx` with a lock (`{votes.xlsx}.lock`) to avoid concurrent writes.
- Reads also retry on `PermissionError`. There is a pre-results cleanup that removes empty rows to guard against partial/appended artifacts.
- The session cookie prevents re-voting per post for the current session only. It does not implement user identity or long-term deduplication.


## 6) Build, Run, and Packaging

- Requirements: Python 3.8+

- Setup
  ```bash
  python -m venv venv
  # Windows
  .\venv\Scripts\activate
  # Install deps
  pip install -r requirements.txt
  ```

- Development run
  ```bash
  python main.py
  # The app prints Local/Network URLs and opens a browser to localhost
  ```

- Packaging (Windows exe)
  ```bash
  pyinstaller --noconsole --add-data "templates;templates" --add-data "static;static" main.py
  # or use the project spec:
  pyinstaller school-election-app.spec
  # Output in dist/school-election-app.exe
  ```


## 7) Security Notes and Limitations

- Intended for local/single-site use (e.g., school LAN). No durable authentication or user provisioning is implemented.
- Admin login is password-only via cookie; change `admin_password` in `config.json` before deployment.
- The session cookie is signed but not encrypted; it only stores flags and a list of posts voted in this session.
- Vote storage is a single Excel file; consider backup/rotation procedures if long-lived.


## 8) Code Quality and Improvement Opportunities

- Persistence
  - Replace Excel with a lightweight DB (SQLite) to improve consistency, concurrent access, and query/reporting.
  - Add transactional semantics and integrity checks.

- Sessions and Auth
  - Persist sessions server-side or introduce a minimal login step for students with unique tokens or roster IDs.
  - Add CSRF protection for form posts (currently relying on simple flow control).

- Validation and UX
  - Enforce unique candidate names per post via config loader; surface validation errors in admin UI.
  - Add configurable per-post voting constraints (e.g., select up to N candidates).

- Admin and Ops
  - Add an authenticated admin dashboard to edit posts/candidates, view live results, reset votes, and download exports.
  - Provide a log directory with structured logs and rotation.

- Deployment
  - Provide cross-platform packaging (Mac/Linux), and a simple installer.
  - Add an environment toggle to bind to `127.0.0.1` only, if required.

- Testing
  - Add unit tests for file ops and results aggregation; template rendering tests for critical pages.


## 9) Development Notes

- Image handling
  - Candidate images are referenced by exact candidate name with `.png` under `static/images/candidates/`. A fallback image (`contact.png`) is used if missing.

- Theming
  - `theme_name` in `config.json` conditionally adjusts navbar/button colors in `base.html` to maintain contrast.

- Single-instance behavior
  - The app uses a lock in the OS temp directory. If it cannot acquire the lock, it attempts to call `/internal-shutdown` on the existing instance, retries, and if still stuck, suggests manual intervention.


## 10) Ready for Next Phase

The codebase is in a clean state with clear separation of templates/static and external settings. It’s suitable to extend with new features. Candidate next-phase features include:

- Role-based admin dashboard (secure edits to posts/candidates, CSV/Excel import, reset tools)
- Switchable persistence (SQLite) with migration tool
- Audit log and basic analytics (turnout per post, voting windows)
- Multi-select posts with constraints (e.g., vote for up to N candidates)
- Network mode toggles and PIN-based student access

Let me know the feature you’d like to build next; the app is ready for iterative development.

