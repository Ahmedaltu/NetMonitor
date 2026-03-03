# app/config/config.py


import yaml

PING_COUNT = 4
PING_TARGET = "8.8.8.8"

def load_config(config_path):
	"""
	Loads a YAML config file and returns a dict with keys expected by the test.
	"""
	with open(config_path, 'r') as f:
		cfg = yaml.safe_load(f)

	# Map config keys to expected test keys
	influx = cfg.get('influx', {})
	ping = cfg.get('ping', {})
	return {
		"ORG": influx.get('org', ''),
		"BUCKET": influx.get('bucket', ''),
		"PING_TARGET": ping.get('target', ''),
		"PING_COUNT": ping.get('count', 0),
		"INTERVAL_SECONDS": cfg.get('interval_seconds', 0),
		"TOKEN": influx.get('token', ''),
	}
