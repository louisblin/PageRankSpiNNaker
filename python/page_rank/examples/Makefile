# Shorthand to run the examples
PYTHON_ROOT := $(CURDIR)/../..
EXAMPLES := $(patsubst $(CURDIR)/%.py, %, $(wildcard $(CURDIR)/*.py))

build:
	$(MAKE) -C $(PYTHON_ROOT)/page_rank/model

$(EXAMPLES): build
	bash -c "export PYTHONPATH=$(PYTHON_ROOT) && python $(CURDIR)/$@.py"