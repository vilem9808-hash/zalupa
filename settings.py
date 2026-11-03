"""User preferences; no changes to the Python installation or game files."""
import json
import math
import os
from pathlib import Path

DEFAULTS={'fullscreen':False,'camera_shake':False,'music_volume':35}


def default_path():
    base=Path(os.environ.get('LOCALAPPDATA') or os.environ.get('XDG_CONFIG_HOME') or str(Path.home()/'.config'))
    return base/'WolfVsRabbit'/'settings.json'


def normalize(raw):
    if not isinstance(raw,dict):return dict(DEFAULTS)
    result={k:raw[k] if isinstance(raw.get(k),bool) else DEFAULTS[k] for k in ('fullscreen','camera_shake')}
    v=raw.get('music_volume',DEFAULTS['music_volume'])
    result['music_volume']=round(max(0,min(100,v))) if isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) else DEFAULTS['music_volume']
    return result


def load(path):
    try:
        raw=json.loads(Path(path).read_text(encoding='utf-8'))
        return normalize(raw)
    except (OSError,ValueError,TypeError):return dict(DEFAULTS)


def save(path,values):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_suffix('.tmp')
    temp.write_text(json.dumps(normalize(values),indent=2),encoding='utf-8')
    temp.replace(path)
