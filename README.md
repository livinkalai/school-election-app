# School Voting System

A simple web-based (no-internet required) voting system for schools to conduct elections.

## Features

- Multiple post selection
- Candidate voting with images
- Immediate results display
- Admin panel for results viewing
- Data saved in Excel format
- Configurable school name and admin credentials

## Configuration

On a new machine or clone, copy `settings/config.example.json` to `settings/config.json` and edit values (school name, admin password, etc.). The repository does not include `config.json` so local credentials are not published.

The application uses the following configuration files in the `settings` folder:

### 1. config.json
```json
{
    "school_name": "Your School Name",    // Change this to your school's name
    "logo_url": "",                       // Optional: URL for school logo
    "background_url": "",                // Optional: URL for background image
    "admin_username": "admin",            // Admin login username
    "admin_password": "admin123",         // Admin login password
    "theme_name": "primary",              // UI theme (options: primary, secondary, light, warning, info)
    "available_themes": ["primary", "secondary", "light", "warning", "info"]
}
```

### 2. candidates.json
```json
{
    "school_people_leader": [
        "John_C_10_A",
        "Sarah_M_11_B"
    ],
    "assistant_school_people_leader": [
        "Mike_R_9_C",
        "Emma_S_10_D"
    ]
}
```

Important notes for candidate names:
- Each candidate name must be unique
- Use the format: `Name_Initial_Class_Section`
  - Example: `John_C_10_A` for John from Class 10-A
  - This helps avoid duplicate names and makes identification easier
- The file will be created automatically with empty lists if it doesn't exist
- Add candidate images in `/static/images/candidates/` with the same name (e.g., `John_C_10_A.png`)

## Candidate Images

1. Place candidate photos in `static/images/candidates/` folder
2. Name format: `candidatename.png`
   - Must match exactly with the candidate names in candidates.json
   - Example: If candidate name is "John", image should be `John.png`
3. If an image is not found, the system will use the default image (`contact.png`)

## Important Notes

1. **File Updates**: If you update any configuration files or images:
   - Close the application completely
   - Make your changes
   - Restart the application
   - Changes will not take effect while the application is running

2. **Image Requirements**:
   - Use PNG format for images
   - Keep image sizes reasonable (recommended: 300x300 pixels)
   - Place default image (`contact.png`) in `static/images/` folder

3. **File Structure**:
```
YourAppFolder/
├── settings/
│   ├── config.json
│   └── candidates.json
├── static/
│   ├── images/
│   │   ├── contact.png
│   │   └── candidates/
│   │       ├── John.png
│   │       └── Jane.png
│   └── ...
└── ...
```

## Installation

1. Download the latest release from the releases page
2. Extract the ZIP file
3. Edit `settings/config.json` to set your school name and admin credentials
4. Edit `settings/candidates.json` to set up your posts and candidates
5. Add candidate images to `static/images/candidates/` folder
6. Run the executable file

## Usage

1. Start the application
2. Enter your name to vote
3. Select the post you want to vote for
4. Choose your candidate
5. View results (admin only)

## Admin Access

To access the admin panel:
1. Enter "admin" as your name
2. Enter the admin password (default: "admin123")
3. You can view results and close the application

## Security Notes

- The application is designed for local network use
- No authentication is implemented
- Votes are stored in Excel format
- Session cookies prevent multiple votes for the same post 

## Common Commands and Troubleshooting

### Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows
.\venv\Scripts\activate

# Linux/Mac
source venv/bin/activate

# Deactivate virtual environment
deactivate
```

### Package Management
```bash
# Install dependencies
pip install -r requirements.txt

# Update pip
python -m pip install --upgrade pip

# List installed packages
pip list

# Export requirements
pip freeze > requirements.txt
```

### Running the Application
```bash
# Development mode
python main.py

# Create executable
pyinstaller --noconsole --add-data "templates;templates" --add-data "static;static" main.py

pyinstaller school-election-app.spec

```

### Troubleshooting
1. If you get "ModuleNotFoundError":
   - Make sure virtual environment is activated
   - Run `pip install -r requirements.txt`

2. If images don't appear:
   - Check if images are in correct folders
   - Verify image names match candidate names exactly
   - Ensure images are in PNG format

3. If configuration changes don't take effect:
   - Close the application completely
   - Make your changes
   - Restart the application

4. If executable doesn't run:
   - Make sure all required files are in the correct folders
   - Check if antivirus is blocking the executable
   - Try running as administrator

## Setup

1. Install Python 3.8 or later
2. Create and activate virtual environment:
   ```
   # Windows
   python -m venv venv
   .\venv\Scripts\activate

   # Linux/Mac
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

## Running the Application

### Development Mode
```
python main.py
```

### Create Windows Executable
```
pyinstaller --noconsole --add-data "templates;templates" --add-data "static;static" main.py
 (or)
pyinstaller school-election-app.spec
```

The executable will be created in the `dist` folder.

## File Structure

- `main.py` - Main application file
- `templates/` - HTML templates
- `static/images/` - Images folder
  - `candidates/` - Candidate photos
  - `contact.png` - Default image
- `settings/` - Configuration files
  - `config.json` - Application settings
  - `candidates.json` - Post and candidate configuration
- `votes.xlsx` - Vote storage (created automatically; columns include `VoteId`, `SourceMachine` for LAN sync)
- `pending_sync.jsonl` - Queued votes when Primary push fails (Secondary only; optional)

## Multi-laptop / LAN sync (optional)

Use this when several laptops run the app on the same Wi‑Fi or LAN and you want consolidated results on one or more **Primary** machines without collecting USB drives.

### `settings/config.json` keys

| Key | Meaning |
|-----|--------|
| `node_role` | `"primary"` or `"secondary"`. Default is **`secondary`** if omitted. |
| `primary_base_urls` | On **secondaries**: list of base URLs of Primary machines, e.g. `["http://192.168.1.10:8001"]`. After each local vote, the app POSTs to these URLs. |
| `secondary_base_urls` | On **primaries**: list of each voting laptop’s base URL for **Collect Now**, e.g. `["http://192.168.1.21:8001"]`. |
| `sync_secret` | Shared password for LAN APIs. **Must be the same on all machines** that sync. If empty, sync is disabled. |
| `machine_id` | Optional label stored with each vote (defaults to the PC hostname). |

### Behaviour

- **Secondaries** save every vote locally, then push a copy to every URL in `primary_base_urls`. If the network fails, votes are queued in `pending_sync.jsonl` and retried every 30 seconds.
- **Primaries** accept pushed votes (`POST /api/votes/ingest`) and expose `GET /api/votes/export` for **Collect Now** (admin results page → **Collect Now** button, Primary only).
- **Collect Now** pulls from each `secondary_base_urls` entry and merges by `VoteId` (no double-counting).
- **Firewall**: allow inbound TCP on port **8001** on Primaries (for push). For Collect Now, allow the Primary to reach each Secondary on **8001** (inbound on secondaries from the LAN).

### Two Primary machines

List both URLs in `primary_base_urls` on every Secondary. Each vote is sent to both. Use the same `sync_secret` everywhere.

### PyInstaller build

`school-election-app.spec` bundles only `settings/config.json` and `settings/candidates.json` (not the whole `settings` tree), so dev-only files under `settings` are not packed into the executable.

## Security Notes

- The application is designed for local network use
- No authentication is implemented
- Votes are stored in Excel format
- Session cookies prevent multiple votes for the same post 
