
VHDMMIO = PYTHONPATH=.. python3 -m vhdmmio

YAML = $(shell find -name '*.mmio.yaml')

.PHONY: all
all: $(YAML:.mmio.yaml=.regfile)

.PHONY: %.build
%.regfile: %.mmio.yaml
	rm -rf $(@D)/html $(@D)/vhdl
	$(VHDMMIO) $< -H $(@D)/html -V $(@D)/vhdl -P $(@D)/vhdl --stacktrace
