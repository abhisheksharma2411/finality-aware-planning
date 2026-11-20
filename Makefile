# FinalityAwarePlanning -- attributing financial agent loss to decisions and to faults.
#
#   make setup        virtualenv, and fetch FinalityBench (P1) if it is absent
#   make test         property tests, including decomposition completeness
#   make experiments  run E1-E6 and write results/
#   make figures      regenerate figures from results/
#   make tables       regenerate LaTeX tables and macros from results/
#   make paper        build paper/fap.pdf
#   make arxiv        build and verify a self-contained arXiv submission
#   make reproduce    all of the above, from a clean tree

PY  := .venv/bin/python
PIP := .venv/bin/pip

.PHONY: setup p1 test experiments figures tables paper arxiv reproduce clean distclean

setup: $(PY) p1

$(PY):
	python3 -m venv .venv
	$(PIP) install --quiet --upgrade pip
	$(PIP) install --quiet -r requirements.txt

# This paper is a causal layer over FinalityBench and does not reimplement it.
# A sibling checkout is used when present; otherwise the released tag is cloned.
# ensure_or_clone() prefers an installed package, then a sibling checkout,
# then vendor/, and fetches the pinned revision if none of those is here.
# stderr is NOT silenced: the old target hid its own ImportError behind
# `2>/dev/null ||` and fell through to a fallback that failed the same way,
# so a fresh clone reported nothing useful.
p1:
	@$(PY) -c "import sys; sys.path.insert(0,'src'); \
	from fap._p1 import ensure_or_clone, p1_provenance; \
	ensure_or_clone(); \
	print('finalitybench:', p1_provenance())"

test: setup
	$(PY) -m pytest

experiments: setup
	cd experiments && ../$(PY) run_all.py

figures: setup
	$(PY) figures/make_figures.py

tables: setup
	$(PY) paper/make_tables.py

paper: tables figures
	cd paper && latexmk -pdf -interaction=nonstopmode -halt-on-error fap.tex
	@echo "built paper/fap.pdf"

arxiv: paper
	$(PY) paper/make_arxiv.py

reproduce: distclean setup test experiments figures tables paper
	@echo
	@echo "reproduce complete -- paper/fap.pdf"

clean:
	rm -rf paper/*.aux paper/*.log paper/*.out paper/*.fls paper/*.fdb_latexmk \
	       paper/*.bbl paper/*.blg .pytest_cache src/**/__pycache__

distclean: clean
	rm -rf results/*.json figures/*.pdf paper/tables paper/numbers.tex paper/fap.pdf
