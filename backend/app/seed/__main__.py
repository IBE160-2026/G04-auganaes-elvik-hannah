import sys

from app.seed import run

# Windows-konsollen bruker en annen kodeside enn UTF-8, og da blir æøå til «�».
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

raise SystemExit(run())
