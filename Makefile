export TOP_DIR :=$(shell git rev-parse --show-toplevel)

export CACTI_BUILD_DIR := $(TOP_DIR)/tools/cacti

CONFIG := $(TOP_DIR)/example_cfgs/freepdk45.cfg

OUT_DIR := $(TOP_DIR)/results

TECH_DIR := $(TOP_DIR)/tech

run:
	./scripts/run.py $(CONFIG) --output_dir $(OUT_DIR) --custom_tech_dir $(TECH_DIR)

view.%:
	klayout ./$(OUT_DIR)/$*/$*.lef &

clean:
	rm -rf ./$(OUT_DIR)

#=======================================
# TOOLS
#=======================================

tools: $(CACTI_BUILD_DIR)

$(CACTI_BUILD_DIR):
	mkdir -p $(@D)
	git clone https://github.com/HewlettPackard/Cacti.git $@
	cd $@; git checkout 1ffd8dfb10303d306ecd8d215320aea07651e878
	cd $@; git apply $(TOP_DIR)/patches/cacti.patch
	sh $(TOP_DIR)/patches/nmlimitremoval_patch.sh
	cd $@; make -j4

clean_tools:
	rm -rf $(CACTI_BUILD_DIR)


debug:
	python3 -m pdb ./scripts/run.py $(CONFIG) --output_dir $(OUT_DIR) --custom_tech_dir $(TECH_DIR)
