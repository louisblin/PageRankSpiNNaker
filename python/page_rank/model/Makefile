# This is expected to run within the Docker images provided with the project.

build:
	bash -c "pip install -r $(CURDIR)/requirements.txt"
	bash -c ". ~/.spinnaker_env && $(MAKE) -C $(CURDIR)/c_models"