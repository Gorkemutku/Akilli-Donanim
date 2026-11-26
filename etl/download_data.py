from importlib import import_module

try:
	kagglehub = import_module("kagglehub")
except ModuleNotFoundError as exc:
	if exc.name != "kagglehub":
		raise
	raise SystemExit("Missing dependency: install it with `python -m pip install kagglehub`.") from exc

# Download latest version
path = kagglehub.dataset_download("sushmita36/laptops-dataset")

print("Path to dataset files:", path)