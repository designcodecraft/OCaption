import json
import os

_DEF = {
    "name": "OCaption",
    "version": "1.0",
    "window_title_template": "{name} v{version}",
    "icon": "assets/icon.ico",
}

def load():
    """Load app metadata from app_meta.json.
    Returns dict with keys: name, version, title, icon (absolute path).
    """
    base_dir = os.path.dirname(__file__)
    cfg_path = os.path.join(base_dir, "app_meta.json")
    cfg = {}
    try:
        with open(cfg_path, "r", encoding="utf-8") as f:
            cfg = json.load(f) or {}
    except Exception:
        cfg = {}

    name = cfg.get("name", _DEF["name"])
    version = cfg.get("version", _DEF["version"])
    tmpl = cfg.get("window_title_template", _DEF["window_title_template"]) or "{name} v{version}"
    title = tmpl.format(name=name, version=version)
    icon_rel = cfg.get("icon", _DEF["icon"]) or _DEF["icon"]
    icon = os.path.join(base_dir, icon_rel) if not os.path.isabs(icon_rel) else icon_rel

    return {"name": name, "version": version, "title": title, "icon": icon}
