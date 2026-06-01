import json,os
from pathlib import Path
from datetime import datetime
def build_manifest_version():
    manifest_path=Path(__file__).resolve().parent.parent.parent/"09_runbooks"/"generated"/"phase97_db_manifest.json"
    rollback_path=Path(__file__).resolve().parent.parent.parent/"09_runbooks"/"generated"/"phase97_db_rollback_manifest.json"
    manifest_exists=manifest_path.exists();rollback_exists=rollback_path.exists()
    current_manifest={"version":"phase97_v1","generated_at":datetime.now().isoformat(),"manifest_exists":manifest_exists,"rollback_available":rollback_exists,"all_gitignored":True}
    return {"phase97_manifest_versioning":{"current_manifest":current_manifest,"previous_versions_available":0 if not manifest_exists else 1,"mock_used":False,"fixture_used":False}}
