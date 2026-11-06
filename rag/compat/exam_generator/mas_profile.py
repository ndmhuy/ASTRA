"""Minimal flag behavior needed by the snapshot; not the product profile."""
def active(config):
    return isinstance(config, dict) and isinstance(config.get('mas'), dict) and config['mas'].get('profile') == 'on'

def rag(config):
    return active(config) and config['mas'].get('rag') in (True, 'true', 'yes', 'on', '1', 'lexical')
