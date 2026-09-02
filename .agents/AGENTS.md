# Workspace Agents Rules

- **Error-Handler Agent**: Forget about the error-handler agent when developing. We haven't planned it yet. Do not attempt to use it or create it.
- **Agent Instructions**: Never hard code instructions to an agent or give object-specific knowledge (like "do this to make a bottle") to build a specific object only to an agent.
- **Run Scripts**: When developing or making changes to `backend/run.py`, always remember to also check and update `desktop_run.py` and `backend/api_run.py`. These files are the actual entry points for the desktop application, and any architectural or startup changes in `run.py` must be mirrored there.
- **Naming Rule**: The application is officially named **FreeGen**, even though the repository is called `sketch2cad`. Always refer to the application as FreeGen in user-facing texts, files, folders, and build outputs.
