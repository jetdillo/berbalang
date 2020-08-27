all: release docker

debug:
	cargo build

release:
	cargo build --release

docker:
	docker build -t pseudosue/berbalang .
	docker push pseudosue/berbalang

docs:
	./rustdoc.sh
