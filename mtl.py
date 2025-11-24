from __future__ import annotations

from pathlib import Path
from typing import Dict, List


def parse_mtl_file(path: Path) -> Dict[str, dict]:
	"""Parse a Wavefront MTL file and return materials keyed by name."""
	materials: Dict[str, dict] = {}
	current_name: str | None = None

	if not path.exists():
		raise FileNotFoundError(f"MTL file not found: {path}")

	with path.open("r", encoding="utf-8", errors="ignore") as stream:
		for raw_line in stream:
			line = raw_line.strip()
			if not line or line.startswith("#"):
				continue

			parts = line.split(None, 1)
			if not parts:
				continue

			keyword = parts[0]
			data = parts[1] if len(parts) > 1 else ""

			if keyword == "newmtl":
				current_name = data.strip()
				if not current_name:
					current_name = None
					continue
				materials[current_name] = {"__source__": str(path)}
				continue

			if current_name is None:
				continue

			material = materials[current_name]

			if keyword in {"Ka", "Kd", "Ks", "Ke"}:
				material[keyword] = _parse_floats(data, expected=3)
			elif keyword in {"Tf"}:
				material[keyword] = _parse_floats(data, expected=3)
			elif keyword in {"Ns", "Ni", "d"}:
				float_values = _parse_floats(data, expected=1)
				material[keyword] = float_values[0] if float_values else None
			elif keyword == "illum":
				int_values = _parse_ints(data, expected=1)
				material[keyword] = int_values[0] if int_values else None
			elif keyword.startswith("map_") or keyword in {"bump", "map_bump"}:
				material[keyword] = data.strip()
			else:
				# Store any other tokens verbatim for potential later use
				material[keyword] = data.strip()

	# Resolve relative texture paths after parsing
	for material in materials.values():
		for key, value in list(material.items()):
			if not key.startswith("map_") and key not in {"bump", "map_bump"}:
				continue
			resolved = _resolve_texture_path(path.parent, value)
			if resolved:
				material[f"{key}_path"] = resolved

	return materials


def _parse_floats(data: str, expected: int | None = None) -> List[float]:
	tokens = [token for token in data.strip().split() if token]
	values: List[float] = []
	for token in tokens:
		try:
			values.append(float(token))
		except ValueError:
			pass
		if expected is not None and len(values) >= expected:
			break
	return values


def _parse_ints(data: str, expected: int | None = None) -> List[int]:
	tokens = [token for token in data.strip().split() if token]
	values: List[int] = []
	for token in tokens:
		try:
			values.append(int(float(token)))
		except ValueError:
			pass
		if expected is not None and len(values) >= expected:
			break
	return values


def _resolve_texture_path(base: Path, raw_value: str | None) -> str | None:
	if not raw_value:
		return None

	value = raw_value.strip().strip('"')
	if not value:
		return None

	candidate = Path(value)
	if not candidate.is_absolute():
		candidate = (base / value).resolve()

	return str(candidate)
