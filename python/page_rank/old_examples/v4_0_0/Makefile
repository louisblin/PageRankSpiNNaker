BUILD_DIRS = hello_world Conways ring page_rank_spin1

all: $(BUILD_DIRS)
	for d in $(BUILD_DIRS); do (cd $$d; "$(MAKE)") || exit $$?; done

clean: $(BUILD_DIRS)
	for d in $(BUILD_DIRS); do (cd $$d; "$(MAKE)" clean) || exit $$?; done

# Forces the execution of whatever depends on it
FORCE:

$(BUILD_DIRS): FORCE
	cd $@; "$(MAKE)" clean all; zsh -c ". ~/.spinnaker_env && ybug 192.168.240.253 < $@.ybug"
