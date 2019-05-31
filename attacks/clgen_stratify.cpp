#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <iostream>
#include <sstream>
#include <math.h>
#include <fstream>
#include <map>
using namespace std;

int CLOSED_SITENUM, CLOSED_INSTNUM, OPEN_INSTNUM, TOTAL_NUM;
map<string, string> d;

int sinste_to_ind(int site, int inst) {
	int ind = 0;
	while (site > CLOSED_SITENUM) {
		site -= CLOSED_SITENUM + 1;
		ind += CLOSED_SITENUM * CLOSED_INSTNUM + OPEN_INSTNUM;
	}
	ind += site * CLOSED_INSTNUM + inst;
	return ind;
}

void load_onefile(double** matrix){
	int webx,weby,trialx,trialy,lengthx,lengthy;
	int dis_int;
	double dis;
	char cruft;

	int line = 0;
	FILE* fin;
	ostringstream ss;
	ss.clear();
	ss.str("");
	ss << d["OUTPUT_LOC"] << "clLev" << "-" << d["LEV_METHOD"] << ".lev";
	if((fin = fopen(ss.str().c_str(), "r")) == NULL){
		printf("cannot open %s for reading\n", ss.str().c_str());
		exit(1);
	}
	while(fscanf(fin, "%d;%d;%d;%d;%d;%d;%d%c", &webx,&trialx,&weby,&trialy,&lengthx,&lengthy,&dis_int,&cruft) == 8){
		int ok = 1;
		if (webx > CLOSED_SITENUM or weby > CLOSED_SITENUM) {
			ok = 0;
		}
		if (webx < CLOSED_SITENUM and trialx >= CLOSED_INSTNUM) {
			ok = 0;
		}
		if (webx == CLOSED_SITENUM and trialx >= OPEN_INSTNUM) {
			ok = 0;
		}
		if (weby < CLOSED_SITENUM and trialy >= CLOSED_INSTNUM) {
			ok = 0;
		}
		if (weby == CLOSED_SITENUM and trialy >= OPEN_INSTNUM) {
			ok = 0;
		}
		if (ok == 0) {
			printf("warning: %d %d %d %d cannot be parsed correctly\n", webx, trialx, weby, trialy);
			exit(1);
		}
		if (ok == 1) {
			dis = dis_int/1000000.0;
			dis = exp(-2*dis*dis); //from clgen_gamma_matrix
			matrix[sinste_to_ind(webx,trialx)][sinste_to_ind(weby,trialy)] = dis;
			matrix[sinste_to_ind(weby,trialy)][sinste_to_ind(webx,trialx)] = dis;
			line++;
			//printf("%d %d %d %d dist: %f\n", webx, trialx, weby, trialy, dis);
		}
	}
	printf("parsing %s finished, lines = %d\n",ss.str().c_str(),line);
	fclose(fin);
}

void stratify(double** matrix){

	int DIM = TOTAL_NUM;
	ostringstream ss;
	FILE *fout[10];
	for (int i = 0; i < 10; i++) {
		ss.clear();
		ss.str("");
		ss << d["OUTPUT_LOC"] << "clLev" << "-" << d["LEV_METHOD"] << "-" << i << ".matrix";
		if ((fout[i] = fopen(ss.str().c_str(), "w")) == NULL) {
			
			cout<<"cannot open file "<<ss.str().c_str()<<endl;
			exit(1);
		}
	}
	for(int web = 1; web <= CLOSED_SITENUM; web++){
		for(int trial = 1; trial <= CLOSED_INSTNUM; trial++){
			int fold = ((trial-1)*10)/CLOSED_INSTNUM;
			fprintf(fout[fold],"%d 0:%d ", web, (web-1)*CLOSED_INSTNUM+trial);
			for(int i = 1; i <= DIM; i++){
				fprintf(fout[fold], "%d:%lf ", i, matrix[(web-1) * CLOSED_INSTNUM + trial-1][i-1]);
			}
			fprintf(fout[fold], "\n");
		}
	}
	int web = CLOSED_SITENUM+1;
	
	for(int trial = 1; trial <= OPEN_INSTNUM; trial++) {
		int fold = ((trial-1)*10)/OPEN_INSTNUM;
		fprintf(fout[fold],"%d 0:%d ", web, CLOSED_SITENUM*CLOSED_INSTNUM+trial);
		for(int i = 1; i <= DIM; i++){
			fprintf(fout[fold], "%d:%lf ", i, matrix[CLOSED_SITENUM * CLOSED_INSTNUM + trial-1][i-1]);
		}
		fprintf(fout[fold], "\n");
	
	}
	for (int i = 0; i < 10; i++) {
		fclose(fout[i]);
	}
}

void read_options(string fname) {
//	std::map <string, string> d;
	ifstream fread;
	fread.open(fname.c_str());
	while (fread.peek() != EOF) {
		string str = "";
		getline(fread, str);
		string optname = str.substr(0, str.find_first_of("\t"));
		string optval = str.substr(str.find_first_of("\t")+1);
		d[optname] = optval;
	}
	fread.close();
}



int main(int argc, char** argv){
	
	char* optionname = argv[1]; //option
	read_options(optionname);

	//we explicitly define those for convenience:
	CLOSED_SITENUM = atoi(d["CLOSED_SITENUM"].c_str());
	CLOSED_INSTNUM = atoi(d["CLOSED_INSTNUM"].c_str());
	OPEN_INSTNUM = atoi(d["OPEN_INSTNUM"].c_str());
	TOTAL_NUM = CLOSED_SITENUM * CLOSED_INSTNUM + OPEN_INSTNUM;

	int dim = TOTAL_NUM;
	int i;
	double** matrix = (double**)malloc(sizeof(double*) * dim);
	for(i = 0; i < dim; i++){
		matrix[i] = (double*)malloc(sizeof(double)* dim);
	}
	for(i = 0; i < dim; i++)
		matrix[i][i] = 0.0f;
	load_onefile(matrix);
	stratify(matrix);
	return 0;
}


