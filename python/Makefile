# Shorthand to run the examples

PageRankModel-%:
	$(eval ROOT := $(shell pwd)/sPyNNaker8PageRankModel)
	bash -c ". ~/.spinnaker_env && $(MAKE) -C $(ROOT)/c_models"
	bash -c "export PYTHONPATH=$(ROOT) && python $(ROOT)/examples/$(patsubst PageRankModel-%,%,$@).py"
