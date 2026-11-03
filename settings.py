"""User preferences; no changes to the Python installation or game files."""
import json
import os
from pathlib import Path

DEFAULTS={'fullscreen':False,'camera_shake':False}


def default_path():
    base=Path(os.environ.get('LOCALAPPDATA') or os.environ.get('XDG_CONFIG_HOME') or str(Path.home()/'.config'))
    return base/'WolfVsRabbit'/'settings.json'


def load(path):
    try:
        raw=json.loads(Path(path).read_text(encoding='utf-8'))
        if not isinstance(raw,dict):return dict(DEFAULTS)
        return {key:raw[key] if isinstance(raw.get(key),bool) else value for key,value in DEFAULTS.items()}
    except (OSError,ValueError,TypeError):return dict(DEFAULTS)


def save(path,values):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix('.tmp')
    temp.write_text(json.dumps({k:bool(values[k]) for k in DEFAULTS},indent=2),encoding='utf-8')
    temp.replace(path)
