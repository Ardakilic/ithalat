# ithalat - every command runs inside Docker (python:3.14-slim + pinned wheels);
# no local Python or pip packages needed. Requires only Docker and make.
#
#   make              # = make all: image, STLs + manifest, self-test, preview
#   make generate     # stl/ithalat-*.stl + build/manifest.json
#   make verify       # measure the STLs (ray casts, slices); exit 1 on failure
#   make preview      # preview/index.html + build/artifact.html (tools/build_preview.py)
#   make site         # _site/: the GitHub Pages layout (preview as index.html + STLs)
#   make image        # (re)build the Docker build image
#   make shell        # interactive shell in the build image
#   make clean        # delete build/ and _site/ (scratch outputs)
#   make distclean    # also delete the committed deliverables (STLs, preview)
#
# Any config.py constant can be overridden per run; pass the SAME GEN_ARGS to
# generate and verify (verify fails on STLs built with other settings):
#   make generate verify GEN_ARGS="--glass-t 0.7"
#   make all GEN_ARGS="--set REST_DEPTH=90 --engrave-face top"
#   make all GEN_ARGS="--height 13 --connector pogo5"   # at 13 mm the USB-C grip no longer clears the rest
# Connector variants (CONNECTORS in config.py; default: pogo + USB-C):
#   make generate verify GEN_ARGS="--connector usbc"
#   make generate verify GEN_ARGS="--set \"CONNECTORS=('pogo5','usbc','jst_sh4')\""
#
# GitHub Actions (.github/workflows/pages.yml) runs `make image`, then
# `make generate verify preview site`, and publishes _site/ to GitHub Pages.

IMAGE    := ithalat-build
SITE     := _site
# Runs as your own uid:gid so the files written into the repo stay yours.
DOCKER_RUN := docker run --rm -u $(shell id -u):$(shell id -g) -v "$(CURDIR)":/app -w /app
GEN_ARGS ?=

.PHONY: all image generate verify preview site shell clean distclean

all: image generate verify preview

image:
	docker build -t $(IMAGE) .

generate: image
	$(DOCKER_RUN) $(IMAGE) python3 generate.py $(GEN_ARGS)

verify: image
	$(DOCKER_RUN) $(IMAGE) python3 tools/verify.py $(GEN_ARGS)

preview: image
	$(DOCKER_RUN) $(IMAGE) python3 tools/build_preview.py

# Assembles the files that are already there (run `make all` first after a change);
# open _site/index.html to check what Pages will serve.
site:
	rm -rf $(SITE)
	mkdir -p $(SITE)/stl
	cp preview/index.html $(SITE)/index.html
	cp stl/*.stl $(SITE)/stl/
	touch $(SITE)/.nojekyll

shell: image
	docker run --rm -it -u $(shell id -u):$(shell id -g) -v "$(CURDIR)":/app -w /app $(IMAGE) bash

clean:
	rm -rf build $(SITE) geometry/__pycache__ tools/__pycache__ __pycache__

distclean: clean
	rm -f stl/ithalat-*.stl preview/index.html
