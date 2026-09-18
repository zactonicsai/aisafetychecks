.PHONY: run test container kind fmt validate examples

run:
	python3 -m app.server

test:
	python3 -m unittest discover -s app/tests -v

container:
	docker compose up --build

kind:
	./scripts/30-kind-create.sh
	./scripts/31-kind-deploy.sh

fmt:
	shfmt -w scripts/*.sh scripts/lib/*.sh 2>/dev/null || true
	tofu fmt -recursive infra/terraform 2>/dev/null || terraform fmt -recursive infra/terraform 2>/dev/null || true

validate:
	./scripts/20-test.sh

examples:
	./scripts/21-test-examples.sh

