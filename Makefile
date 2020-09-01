# Render all notes into pdfs for easier reading

KNITTER := scripts/knit.sh

NOTES = $(shell find * -type f -name '*.md' -not -name '*-render*' -not -path '*/.*' -not -path '*/templates/*' | sort -V)
TEMPLATES = $(shell find templates -type f)
ODT = $(shell find * -type f -name '*.odt' -not -path '*/.*' | sort -V)
DOC = $(shell find * -type f -name '*.docx' -not -path '*/.*' | sort -V)
PP = $(shell find * -type f -name '*.pptx' -not -path '*/.*' | sort -V)
MD = $(patsubst %.md,%.pdf,$(NOTES))
PPTX = $(patsubst %.pptx,%.pdf,$(PP))
WRITE = $(patsubst %.odt,%.pdf,$(ODT)) $(patsubst %.docx,%.pdf,$(DOC))

.PHONEY: notes pp write all clean clean-notes clean-pp clean-write

all: notes pp write
notes: $(MD)
pp: $(PPTX)
write: $(WRITE)
clean: clean-notes

%.pdf: %.md
	$(KNITTER) $< $@

-include $(NOTES:%.md=.bin/%-render.md.dep)

%.pdf: %.pptx
	unoconv -f pdf "$<"

%.pdf: %.docx
	libreoffice --headless --convert-to pdf --outdir $(shell dirname $<) $<

%.pdf: %.odt
	libreoffice --headless --convert-to pdf --outdir $(shell dirname $<) $<

clean-notes:
	@rm -rfv $(MD) .bin
clean-pp:
	@rm -fv $(PPTX)
clean-write:
	@rm -fv $(WRITE)
clean-all: clean-notes clean-pp
