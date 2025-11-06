#!/usr/bin/env python3
"""
translate_obj.py

Script simple para aplicar una traslación a todos los vértices de un archivo OBJ
y generar un nuevo archivo OBJ con las posiciones trasladadas.

Uso:
    python translate_obj.py -i input.obj -o output.obj -t 0 -10 0

Conserva todas las demás líneas del OBJ (vt, vn, f, mtllib, etc.).
Las normales no se modifican (la traslación no las afecta).
"""
import argparse
import re
from pathlib import Path

VERTEX_RE = re.compile(r"^(?P<prefix>\s*v\s+)(?P<coords>[-+eE0-9.,\s]+)(?P<suffix>.*)$")


def parse_floats_from_string(s):
    # split by whitespace and filter out empty tokens
    tokens = [t for t in s.strip().split() if t]
    return [float(t) for t in tokens]


def format_floats_to_string(floats, precision=6):
    fmt = ("{:.%df}" % precision)
    return " ".join(fmt.format(f) for f in floats)


def translate_obj(input_path: Path, output_path: Path, tx: float, ty: float, tz: float):
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    with input_path.open('r', encoding='utf-8', errors='ignore') as fin, output_path.open('w', encoding='utf-8') as fout:
        for line in fin:
            m = VERTEX_RE.match(line)
            if m:
                coords_str = m.group('coords')
                try:
                    vals = parse_floats_from_string(coords_str)
                except ValueError:
                    # If parse fails, write original line
                    fout.write(line)
                    continue

                # Only process if at least 3 components
                if len(vals) >= 3:
                    vals[0] = vals[0] + tx
                    vals[1] = vals[1] + ty
                    vals[2] = vals[2] + tz
                    coords_out = format_floats_to_string(vals[:3])
                    # Preserve any suffix/comments after the numbers
                    suffix = m.group('suffix') or ''
                    fout.write(f"{m.group('prefix')}{coords_out}{suffix}\n")
                    continue
                else:
                    # Not enough components, pass through
                    fout.write(line)
            else:
                # Non-vertex line: copy as-is
                fout.write(line)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description='Traslada las coordenadas v de un OBJ y escribe otro OBJ')
    p.add_argument('-i', '--input', required=True, help='Archivo OBJ de entrada')
    p.add_argument('-o', '--output', required=True, help='Archivo OBJ de salida')
    p.add_argument('-t', '--translate', nargs=3, type=float, metavar=('TX','TY','TZ'), required=True,
                   help='Traslación a aplicar (ej: -t 0 -10 0)')
    p.add_argument('--precision', type=int, default=6, help='Decimales en la salida (por defecto 6)')
    args = p.parse_args()

    input_path = Path(args.input)
    output_path = Path(args.output)
    tx, ty, tz = args.translate

    # call
    translate_obj(input_path, output_path, tx, ty, tz)
    print(f"Escrito: {output_path} (trasladado {tx}, {ty}, {tz})")
