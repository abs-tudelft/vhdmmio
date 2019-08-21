
VHDMMIO = PYTHONPATH=.. python3 -m vhdmmio

YAML = $(shell find -name '*.yaml')

.PHONY: all
all: $(YAML:.yaml=.regfile)

.PHONY: %.build
%.regfile: %.yaml
	rm -rf $(@D)/html $(@D)/vhdl
	$(VHDMMIO) $< -H $(@D)/html -V $(@D)/vhdl -P $(@D)/vhdl --stacktrace
