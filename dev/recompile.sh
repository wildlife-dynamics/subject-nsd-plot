#!/bin/bash
# Recompile spec.yaml into ecoscope-workflows-subject-nsd-plot-workflow/ (the same commands Ecoscope Studio runs).
#   ./dev/recompile.sh --install   the first time: a new lock file, and the packages installed
#   ./dev/recompile.sh --update    after that: keeps the lock file and bumps VERSION.yaml

flags=$*

pixi update --manifest-path pixi.toml

# (re)initialize dot executable to ensure graphviz is available
pixi run --manifest-path pixi.toml dot -c

echo "recompiling spec.yaml with flags '--clobber ${flags}'"

command="pixi run --manifest-path pixi.toml \
wt-compiler compile --spec spec.yaml \
--pkg-name-prefix=ecoscope-workflows \
--results-env-var=ECOSCOPE_WORKFLOWS_RESULTS \
--no-progress \
--clobber ${flags}"

exec $command
