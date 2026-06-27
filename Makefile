IMAGE := hcl-playground

.PHONY: run build secure test e2e

## run: build + run locally on http://localhost:8080
run: build
	docker run --rm -p 8080:8080 $(IMAGE)

build:
	docker build -t $(IMAGE) .

## secure: same, but with the container hardening applied (read-only fs, no caps,
## memory/pid limits). The app is offline by design, so normal port networking is fine.
secure: build
	docker run --rm -p 8080:8080 \
		--read-only --tmpfs /scratch:uid=1000 --tmpfs /tmp \
		--cap-drop ALL --security-opt no-new-privileges \
		--memory 1g --pids-limit 256 \
		$(IMAGE)

## test: build with dev deps and run the unit tests in the container
test:
	docker build --build-arg INSTALL_DEV_DEPS=true -t $(IMAGE):test .
	docker run --rm $(IMAGE):test python -m pytest -p no:cacheprovider

## e2e: run Cypress against a running instance (needs `make run` in another shell)
e2e:
	npx cypress run
