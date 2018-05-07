BUILD_DIRS = heat_demo hello_world page_rank

all: $(BUILD_DIRS)
	for d in $(BUILD_DIRS); do (cd $$d; "$(MAKE)") || exit $$?; done

clean: $(BUILD_DIRS)
	for d in $(BUILD_DIRS); do (cd $$d; "$(MAKE)" clean) || exit $$?; done

# Forces the execution of whatever depends on it
FORCE:

$(BUILD_DIRS): FORCE
	(cd $@; "$(MAKE)") || exit $$?
	python $@/$@.py