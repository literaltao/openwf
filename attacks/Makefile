all: flearner dist clLev clgen_stratify

flearner: flearner.cpp
	g++ flearner.cpp -o flearner

dist: dist.cpp
	mpiCC dist.cpp -o dist

clLev: clLev.cpp
	mpiCC clLev.cpp -o clLev

clgen_stratify: clgen_stratify.cpp
	g++ clgen_stratify.cpp -o clgen_stratify

clean:
	rm flearner dist clLev clgen_stratify
