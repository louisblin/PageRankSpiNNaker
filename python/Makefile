# Shorthand to run the examples

PageRankModel-%:
	$(eval ROOT := $(shell pwd)/sPyNNaker8NewModelTemplate)
	$(MAKE) -C $(ROOT)/c_models
	zsh -c "cd $(ROOT) && export PYTHONPATH=$(ROOT) && python examples/$(patsubst PageRankModel-%,%,$@).py"
