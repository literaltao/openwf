#include <mpi.h>
#include <stdio.h>
#include <errno.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include <sys/time.h>
#include <vector>
#include <algorithm>
#include <time.h>
#include <iostream>
#include <map>
#include <fstream>
#include <sstream>
using namespace std;

//Uses mpi to output pairwise distances between packet sequences
//for several attacks (DIST_FEAT = 1), requires extracted feature files to be present
//outputs to a predist file

//to fix the size issue, this is currently designed to deal with 100x100+10000

//call extractors (e.g. Pa-CUMUL-extractor-dist.py) to get extracted features (needed for PaC, PaF, kNN)

//we -do not- calculate the distance between anything with open elements


typedef struct _cord{
	int x;
	int y;
}CORD;

int CORE, CORE_TOTAL, TOTAL_NUM;
int CLOSED_SITENUM, CLOSED_INSTNUM, OPEN_INSTNUM, CLOSED_FOLD_TOTAL, OPEN_FOLD_TOTAL;
map<string, string> d;

double stat_cc(double*, double*, int);

class Cellset{

public:
	vector<double> buffer; //temporary storage when parsing cells/data
	vector<int> bufferi; //as above, though only for cells
	//to parse into cells, it alternates between time and lengths
	vector<int> sizes;
	vector<double*> pool;
	vector<double*> cell_t;
	vector<int*> cell_l;
	vector<string> pool_names;
public:
	Cellset(int); //calls Parse_data or Parse_cells to populate pool
	~Cellset();
	CORD inverse_cantor(int z);
	
	int Parse_data(char* fname); //uses buffer to push file data into pool
	void Parse_cells(char* fname); //uses buffer to push file data into cell_l and cell_t
	double* fetch_pool(int index);
	int fetch_sizes(int index);
	double* fetch_cell_t(int index);
	int* fetch_cell_l(int index);
	string fetch_pool_name(int index);
	double dist(int index1, int index2);
};

Cellset::Cellset(int is_parse_cells){
	
	pool.clear();
	cell_l.clear();
	cell_t.clear();
	buffer.clear();
	sizes.clear();

	string folder = d["DATA_LOC"];

	char fname[300];

	int count = 0;
	int progcount = 0;

	for (int s = 0; s < CLOSED_SITENUM; s++) {
		for (int i = 0; i < CLOSED_INSTNUM; i++) {
			sprintf(fname,"%s%d-%d.cell", folder.c_str(),s,i);
			string strfname = (string)fname;
			if (d["ATTACK_NAME"] == "Pa-FeaturesSVM.py") {
				strfname += "PaF";
			}
			if (d["ATTACK_NAME"] == "Pa-CUMUL.py") {
				strfname += "PaC";
			}
			if (d["ATTACK_NAME"] == "Wa-kNN.py") {
				strfname += "kNN";
			}
			char* cstrfname = strdup(strfname.c_str());
			if (is_parse_cells == 1) Parse_cells(cstrfname);
			if (is_parse_cells == 0) Parse_data(cstrfname);
			pool_names.push_back(strfname);
			count += 1;
			if ((count * 10) / (CLOSED_SITENUM * CLOSED_INSTNUM) > progcount) {
				printf("Loaded %d closed\n", count);
				progcount += 1;
			}
		}
	}

	count = 0;
	progcount = 0;
	for(int i = 0; i < OPEN_INSTNUM; i++){
		sprintf(fname,"%s%d.cell", folder.c_str(),i);
		string strfname = (string)fname;
		if (d["ATTACK_NAME"] == "Pa-FeaturesSVM.py") {
			strfname += "PaF";
		}
		if (d["ATTACK_NAME"] == "Pa-CUMUL.py") {
			strfname += "PaC";
		}
		if (d["ATTACK_NAME"] == "Wa-kNN.py") {
			strfname += "kNN";
		}
		char* cstrfname = strdup(strfname.c_str());
		if (is_parse_cells == 1) Parse_cells(cstrfname);
		if (is_parse_cells == 0) Parse_data(cstrfname);
		pool_names.push_back(strfname);
		count += 1;
		if ((count * 10) / (OPEN_INSTNUM) > progcount) {
			printf("Loaded %d open\n", count);
			progcount += 1;
		}
	}
}

Cellset::~Cellset(){
	for(int i = 0; i < pool.size();i++) {
		delete[] pool.at(i);
	}
	for (int i = 0; i < cell_l.size(); i++) {	
		delete[] cell_t.at(i);	
		delete[] cell_l.at(i);
	}
}

double* Cellset::fetch_pool(int index){
	if(index >= pool.size()){
		printf("fetch_pool error [index=%d poolsize=%lu]", index, pool.size());
		exit(-1);
	}
	return pool.at(index);
}

int* Cellset::fetch_cell_l(int index) {
	if(index >= cell_l.size()){
		printf("fetch_cell_l error [index=%d poolsize=%lu]", index, cell_l.size());
		exit(-1);
	}
	return cell_l.at(index);

}

double* Cellset::fetch_cell_t(int index){
	if(index >= cell_t.size()){
		printf("fetch_cell_t error [index=%d poolsize=%lu]", index, cell_t.size());
		exit(-1);
	}
	return cell_t.at(index);
}

int Cellset::fetch_sizes(int index){
	if(index >= sizes.size()){
		printf("sizes error [index=%d poolsize=%lu]", index, sizes.size());
		exit(-1);
	}
	return sizes.at(index);
}

int Cellset::Parse_data(char *fname){
	FILE* fp = NULL;
	double d;	
	buffer.clear();
	fp = fopen(fname, "r");
	if (!fp) {
		printf("Cannot open %s\n", fname);
		exit(-1);
	}
	while(!feof(fp)){
		int matched = fscanf(fp,"%lf",&d);
		if (matched == 1) {
			buffer.push_back(d);
		}
	}
	fclose(fp);

	double* tmp = new double[buffer.size()];
	for(int x = 0; x < buffer.size(); x++) {
		tmp[x] = buffer.at(x);
	}
	pool.push_back(tmp);
	sizes.push_back(buffer.size());
	return 0;
}

void Cellset::Parse_cells(char *fname){
	FILE* fp = NULL;
	double t;
	int l;
	buffer.clear();
	bufferi.clear();
	
	fp = fopen(fname, "r");
	if (!fp) {
		printf("Cannot open %s\n", fname);
		exit(-1);
	}
	while(!feof(fp)){
		int matched = fscanf(fp,"%lf\t%d\n",&t,&l);
		if (matched == 2) {
			buffer.push_back(t);
			bufferi.push_back(l);
		}
	}
	fclose(fp);

	double* tmp = new double[buffer.size()];
	int* tmpi = new int[buffer.size()];
	for(int x = 0; x < buffer.size(); x++) {
		tmp[x] = buffer.at(x);
		tmpi[x] = bufferi.at(x);
	}
	cell_t.push_back(tmp);
	cell_l.push_back(tmpi);
	sizes.push_back(buffer.size());
}

double minimum(double a, double b, double c){
	double min = a;
	if(b < min)
		min = b;
	if(c < min)
		min = c;

	return min;
}

double DLdis(int* cella, int* cellb, int sizea, int sizeb, int method){

//method 0: Lu-Lev
//method 1: Ca-OSAD
//method 2: Wa-OSAD

	double ret = 0;
	int sizemin = sizea < sizeb? sizea : sizeb;
	int i,j;
    	float subcost,transcost;

	float** dis = new float*[sizea];
	for (i = 0; i < sizea; i++) dis[i] = new float[sizeb];
	for (i = 0; i < sizea; i++) dis[i][0] = i * 2;
	for (j = 0; j < sizeb; j++) dis[0][j] = j * 2;
	
	int db;
	float P = 0;

	float idcost[2] = {2, 2};
	
	if (method == 2)
		idcost[0] = 6;
	
	if (method == 2)
		subcost = 20;
	else
		subcost = 2;

	if (method == 1)
		transcost = 0.1;

	if (method == 0) //Lu-Lev doesn't allow transpositions
		transcost = 100;

	for (i = 1; i < sizea; i++) {
		db = 0;
		for (j = 1; j < sizeb; j++) {
			if (method == 2) {
				P = (float)i/sizea > (float)j/sizeb ? (float)j/sizeb : (float)i/sizea;
				transcost = (1-P*0.9) * (1-P*0.9); //goes from 1 to 0.01;
			}
			if (cella[i] == cellb[j]) {
				dis[i][j] = minimum (
					dis[i-1][j] + idcost[(cella[i] > 0 ? 0 : 1)], //abs(str1[i]),  // a deletion
        	        		dis[i][j-1] + idcost[(cellb[j] > 0 ? 0 : 1)], //abs(str2[j]),  // an insertion
        	        		dis[i-1][j-1] // a substitution
				);
				db = j;
			}
			else {
				dis[i][j] = minimum (
					dis[i-1][j] + idcost[(cella[i] > 0 ? 0 : 1)], //abs(str1[i]),  // a deletion
        	 	       		dis[i][j-1] + idcost[(cellb[j] > 0 ? 0 : 1)], //abs(str2[j]),  // an insertion
        		        	dis[i-1][j-1] + subcost // a substitution
				);
				if(i > 1 && j > 1 && cella[i] == cellb[j-1] && cella[i-1] == cellb[j]) {
					dis[i][j] = 	dis[i][j] < dis[i-2][j-2] + transcost ? 
							dis[i][j] : dis[i-2][j-2] + transcost;
				}
			}
			//printf("%d %d %d %d \n", i, j, dis[i][j], dis);
		}
	}
	ret = dis[sizea-1][sizeb-1]/sizemin;

	for(i = 0 ; i < sizea; i++) {
		delete[] dis[i];
	}
	delete[] dis;

	return ret;
}

double Cellset::dist(int inda, int indb) {
	//returns distance between instances at inda and indb
	int sizea = sizes.at(inda);
	int sizeb = sizes.at(indb);
	//printf("dist %d %d %d %d\n", inda, indb, sizea, sizeb);

	double my_dist = 0;

	if (d["ATTACK_NAME"] == "cc.py") { //cc
		int* cella = fetch_cell_l(inda);
		double* cella_t = fetch_cell_t(inda);
		int* cellb = fetch_cell_l(indb);
		double* cellb_t = fetch_cell_t(indb);

		int minlen = sizea;
		if (sizea > sizeb) minlen = sizeb;

		//first, convert lengths to doubles because stat_cc can only handle doubles
		double* cella_double = new double[minlen];
		for (int i = 0; i < minlen; i++) {
			cella_double[i] = (double)cella[i];
		}
		double* cellb_double = new double[minlen];
		for (int i = 0; i < minlen; i++) {
			cellb_double[i] = (double)cellb[i];
		}
		/*printf("test %f %f %f %f\n", cella_double[0], cella_double[1], cella_double[2], cella_double[3]);
		printf("test2 %d %d %d %d\n", cella[0], cella[1], cella[2], cella[3]);
		printf("test3 %f %f %f %f\n", cella_t[0], cella_t[1], cella_t[2], cella_t[3]);*/

		//printf("test %d %d %lf %lf\n", inda, indb, stat_cc(cella_double, cellb_double, minlen), stat_cc(cella_t, cellb_t, minlen));
	
		my_dist = 1 - stat_cc(cella_double, cellb_double, minlen) * stat_cc(cella_t, cellb_t, minlen);
		delete cella_double;
		delete cellb_double;
	}
	
	if (d["ATTACK_NAME"] == "Pa-FeaturesSVM.py") {
		double* feata = fetch_pool(inda);
		double* featb = fetch_pool(indb);
		int minlen = sizea;
		if (sizea > sizeb) minlen = sizeb;

		my_dist = 0;
		for (int i = 0; i < minlen; i++) {
			my_dist += pow(feata[i] - featb[i], 2);
		}
		//printf("my_dist %f %d\n", my_dist, minlen);
		//my_dist = 1 - exp(-0.0000001 * my_dist);
	}
	
	if (d["ATTACK_NAME"] == "Pa-CUMUL.py") {
		double* feata = fetch_pool(inda);
		double* featb = fetch_pool(indb);

		int minlen = sizea;
		if (sizea > sizeb) minlen = sizeb;

		my_dist = 0;
		for (int i = 0; i < minlen; i++) {
			my_dist += pow(feata[i] - featb[i], 2);
		}
		//printf("my_dist %f %d\n", my_dist, minlen);
		//my_dist = 1 - exp(-0.0001 * my_dist);
	}

	if (d["ATTACK_NAME"] == "Wa-kNN.py") {
		double* feata = fetch_pool(inda);
		double* featb = fetch_pool(indb);

		//read weights
		vector<double> weights;

		FILE * fweight = fopen("weights", "r");
		double weight;
		while(!feof(fweight)){
			if(0 > fscanf(fweight,"%lf",&weight))
				continue;
			weights.push_back(weight);
		}
		fclose(fweight);

		my_dist = 0;
		for (int i = 0; i < weights.size(); i++) {
			my_dist += weights[i] * fabs(feata[i] - featb[i]);
		}
	}

	if (d["ATTACK_NAME"] == "Ca-OSAD.cpp") {
		int* cella = fetch_cell_l(inda);
		int* cellb = fetch_cell_l(indb);
		my_dist = DLdis(cella, cellb, sizea, sizeb, 1);
	}

	if (d["ATTACK_NAME"] == "Wa-OSAD.cpp") {
		int* cella = fetch_cell_l(inda);
		int* cellb = fetch_cell_l(indb);
		my_dist = DLdis(cella, cellb, sizea, sizeb, 2);
	}

	if (d["ATTACK_NAME"] == "Lu-Lev.cpp") {
		int* cella = fetch_cell_l(inda);
		int* cellb = fetch_cell_l(indb);
		int possizea, possizeb, negsizea, negsizeb = 0;
		int* poscella;
		int* poscellb;
		int* negcella;
		int* negcellb;
		vector<int> posbuffer;
		vector<int> negbuffer;
		for (int i = 0; i < sizea; i++) {
			if (cella[i] > 0) posbuffer.push_back(cella[i]);
			if (cella[i] < 0) negbuffer.push_back(cella[i]);
		}
		possizea = posbuffer.size();
		negsizea = negbuffer.size();
		poscella = new int[possizea];
		negcella = new int[negsizea];
		for (int i = 0; i < possizea; i++) poscella[i] = posbuffer.at(i);
		for (int i = 0; i < negsizea; i++) negcella[i] = negbuffer.at(i);
		
		posbuffer.clear();
		negbuffer.clear();
		for (int i = 0; i < sizeb; i++) {
			if (cellb[i] > 0) posbuffer.push_back(cellb[i]);
			if (cellb[i] < 0) negbuffer.push_back(cellb[i]);
		}
		possizeb = posbuffer.size();
		negsizeb = negbuffer.size();
		poscellb = new int[possizeb];
		negcellb = new int[negsizeb];
		for (int i = 0; i < possizeb; i++) poscellb[i] = posbuffer.at(i);
		for (int i = 0; i < negsizeb; i++) negcellb[i] = negbuffer.at(i);

		my_dist = DLdis(poscella, poscellb, possizea, possizeb, 0) * 0.6;
		my_dist += DLdis(negcella, negcellb, negsizea, negsizeb, 0) * 0.4;

		delete [] poscella;
		delete [] poscellb;
		delete [] negcella;
		delete [] negcellb;
	}
		

	//printf("dist returns %d %d %f\n", inda, indb, my_dist);
	return my_dist;
}

double stat_mean(double* seq, int size) {
	double sum = 0;
	for (int i = 0; i < size; i++) {
		sum += seq[i];
	}
	sum /= size;
	return sum;
}

double stat_std(double* seq, int size) {
	double sum = 0;
	double mean = stat_mean(seq, size);
	for (int i = 0; i < size; i++) {
		sum += (seq[i] - mean) * (seq[i] - mean);
	}
	sum /= size;
	sum = pow(sum, 0.5);
	return sum;
}

double stat_cc(double* seqa, double* seqb, int size) {
	double cc = 0;
	double seqa_mean = stat_mean(seqa, size);
	double seqb_mean = stat_mean(seqb, size);
	
	for (int i = 0; i < size; i++) {
		cc += (seqa[i] - seqa_mean) * (seqb[i] - seqb_mean);
	}
	double seqa_std = stat_std(seqa, size);
	double seqb_std = stat_std(seqb, size);
	//printf("%f %f %f %f %f\n", cc, seqa_std, seqb_std, seqa_mean, seqb_mean);
	if (seqa_std != 0) cc /= seqa_std;
	if (seqb_std != 0) cc /= seqb_std;
	cc /= size;
	return cc;

}

void read_options(string fname) {
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

string itoa(int val) {
	string ret;
	ostringstream converter;
	converter << val;
	ret = converter.str();
	return ret;
}

vector<int> job_to_jobxy(int jobind) {
	vector<int> jobxy;
	if (jobind >= OPEN_INSTNUM * (CLOSED_SITENUM * CLOSED_INSTNUM)) {
		jobind -= OPEN_INSTNUM * CLOSED_SITENUM * CLOSED_INSTNUM;
		int w = (int)((sqrt(8*jobind + 1) -1)/2.0);
		int t = (w * w + w)/2;
		int y = jobind - t;
		int x = w - y;
		jobxy.push_back(CLOSED_SITENUM * CLOSED_INSTNUM - 1 - x);
		jobxy.push_back(y);
	}
	else {
		int x = jobind % (OPEN_INSTNUM) + CLOSED_INSTNUM * CLOSED_SITENUM;
		int y = jobind / (OPEN_INSTNUM);
		jobxy.push_back(x);
		jobxy.push_back(y);
	}
	return jobxy;
}

vector< vector<int> > make_joblist() {
	//there are a total of CLOSED_SITENUM * CLOSED_INSTNUM + OPEN_INSTNUM pages
	//we divide it into FOLD_TOTAL subsets, and compute distances only between instances in neighboring subsets (edge case: skip one subset)
	
	vector< vector<int> > joblist;

	for (int x = 0; x < CLOSED_SITENUM * CLOSED_INSTNUM; x++) {
		int my_fold, tar_closed_fold;
		my_fold = (x % CLOSED_INSTNUM) / (CLOSED_INSTNUM / CLOSED_FOLD_TOTAL);
		for (int s2 = 0; s2 < CLOSED_SITENUM; s2++) {
			for (int t2 = my_fold * (CLOSED_INSTNUM/CLOSED_FOLD_TOTAL); 
			t2 < (my_fold+1) * (CLOSED_INSTNUM/CLOSED_FOLD_TOTAL); t2++) {
				vector<int> jobxy;
				jobxy.push_back(x);
				int y = s2 * CLOSED_INSTNUM + t2;
				jobxy.push_back(y);
				joblist.push_back(jobxy);
			}
		}
/*
		//bonus for specific closed_fold
		if ((tar_closed_fold == 1 and CLOSED_FOLD_TOTAL >= 3) or tar_closed_fold == CLOSED_FOLD_TOTAL-2) {
			tar_closed_fold += 1;
			for (int s2 = 0; s2 < CLOSED_SITENUM; s2++) {
				for (int t2 = tar_closed_fold * (CLOSED_INSTNUM/CLOSED_FOLD_TOTAL); 
				t2 < (tar_closed_fold+1) * (CLOSED_INSTNUM/CLOSED_FOLD_TOTAL); t2++) {
					vector<int> jobxy;
					jobxy.push_back(x);
					int y = s2 * CLOSED_INSTNUM + t2;
					jobxy.push_back(y);
					joblist.push_back(jobxy);
				}
			}
		}	
		if (OPEN_INSTNUM > 0 and OPEN_FOLD_TOTAL > 0) {
			if (tar_open_fold < OPEN_FOLD_TOTAL) {
				for (int t2 = tar_open_fold * (OPEN_INSTNUM/OPEN_FOLD_TOTAL); t2 < (tar_open_fold + 1) * (OPEN_INSTNUM/OPEN_FOLD_TOTAL); t2++) {
					vector<int> jobxy;
					jobxy.push_back(x);
					int y = CLOSED_SITENUM * CLOSED_INSTNUM + t2;
					jobxy.push_back(y);
					joblist.push_back(jobxy);
				}
			}
			//bonus for specific open_fold
			if ((tar_open_fold == 1 and OPEN_FOLD_TOTAL >= 3) or tar_open_fold == OPEN_FOLD_TOTAL-2) {
				tar_open_fold += 1;
				for (int t2 = tar_open_fold * (OPEN_INSTNUM/OPEN_FOLD_TOTAL); t2 < (tar_open_fold + 1) * (OPEN_INSTNUM/OPEN_FOLD_TOTAL); t2++) {
					vector<int> jobxy;
					jobxy.push_back(x);
					int y = CLOSED_SITENUM * CLOSED_INSTNUM + t2;
					jobxy.push_back(y);
					joblist.push_back(jobxy);
				}
			}
		}*/
	}

	return joblist;

}


int main(int argc, char** argv){
//

	if(argc != 2){
	    cout <<"call: ./dist <option name>"<<endl;
	    exit(-1);
	}

	MPI_Init(&argc, &argv);
	MPI_Comm_rank(MPI_COMM_WORLD, &CORE);
	MPI_Comm_size(MPI_COMM_WORLD, &CORE_TOTAL);
	//printf("this core=%d total cores=%d\n", CORE, CORE_TOTAL);

	char* optionname = argv[1];
	
	read_options(string(optionname));

	CLOSED_SITENUM = atoi(d["CLOSED_SITENUM"].c_str());
	CLOSED_INSTNUM = atoi(d["CLOSED_INSTNUM"].c_str());
	OPEN_INSTNUM = atoi(d["OPEN_INSTNUM"].c_str());
	CLOSED_FOLD_TOTAL = atoi(d["CLOSED_FOLD_TOTAL"].c_str());
	OPEN_FOLD_TOTAL = atoi(d["OPEN_FOLD_TOTAL"].c_str());

	//load the data set. 
	int parse_cells = 0;
	if (not(d["ATTACK_NAME"] == "Pa-FeaturesSVM.py" or
		d["ATTACK_NAME"] == "Pa-CUMUL.py" or
		d["ATTACK_NAME"] == "Wa-kNN.py")) {
		parse_cells = 1;
	}
	Cellset my_cellset(parse_cells);


	TOTAL_NUM = my_cellset.pool_names.size();
	printf("Pool size is %d\n", my_cellset.sizes.size());
	//if I am the master, check output file and load it:
	if (CORE == 0) {
		FILE * fp = NULL;
		string fname;
		fname = d["OUTPUT_LOC"] + d["ATTACK_NAME"] + ".predist";
		//resumption feature disabled
		/*string fnameout;
		fnameout = fname + ".bak";
		FILE * fout = fopen(fnameout.c_str(), "w");
		if(fp){
			printf("Input file %s found, loading from input file\n", fname.c_str());
			int si1, si2;
			char * garb = new char[500];
			while (fscanf(fp, "%d;%d;%s\n", &si1, &si2,garb) == 3) {
				int job_i[] = {si1, si2};
				vector<int> job (job_i, job_i + sizeof(job_i)/sizeof(int));
				vector<vector<int> >::iterator it;
				it = find(joblist.begin(), joblist.end(), job);
				int index = distance(joblist.begin(), it);
				if (index < joblist.end() - joblist.begin()) {
					joblist.erase(joblist.begin()+index);
					fprintf(fout, "%d;%d;%s\n",si1,si2,garb);
				}
			}
			delete garb;
			fclose(fp);
			fclose(fout);
			rename(fnameout.c_str(), fname.c_str());
		}
		else {
			printf("Input file %s not found, starting anew\n", fname.c_str());
		}*/

		int jobsent = 0;
		int jobdone = 0;
		vector< vector<int> > joblist = make_joblist();
		int jobtotal = joblist.size();
		printf("Job list has length %d, now initiating\n", jobtotal);

		printf("Writing to %s\n", fname.c_str());
		fp = fopen(fname.c_str(), "w");
		if(!fp){
			cout<<"cannot open file " << fname << endl;
			exit(1);
		}

		MPI_Request * request;
		request = new MPI_Request[CORE_TOTAL];
		double ** buf;
		buf = new double*[CORE_TOTAL];
		for (int i = 0; i < CORE_TOTAL; i++) {
			buf[i] = new double[3];
		}
		int tag = 42;
		int talking_core = 1;
		int exit_request[2] = {-1, -1};
		int waiting_cores = 0; //normally equals CORE_TOTAL-1, but in edge cases might be smaller

		for (talking_core = 1; talking_core < CORE_TOTAL; talking_core++) {
			if (jobsent < jobtotal) {
				vector<int> jobxy = joblist[jobsent];
				int my_job[2] = {jobxy[0], jobxy[1]};
				//printf("%d tells %d to do job %d %d\n", 0, talking_core, my_job[0], my_job[1]);
				MPI_Send(my_job, 2, MPI_INT, talking_core, tag, MPI_COMM_WORLD);
				MPI_Irecv(buf[talking_core], 3, MPI_DOUBLE, talking_core, tag, MPI_COMM_WORLD, &request[talking_core]);
				waiting_cores += 1;
				jobsent += 1;
			}
			else MPI_Send(exit_request, 2, MPI_INT, talking_core, tag, MPI_COMM_WORLD);
		}
		//printf("Sent %d jobs\n", jobsent);
		
		//printf("0 has sent all requests, now waiting for replies\n");

		clock_t t1;
		while (jobdone < jobtotal) {
			MPI_Status status;
			int talking_core;
			//printf("now waiting %d %d\n", jobsent, jobdone);
			MPI_Waitany(waiting_cores, &request[1], &talking_core, &status);
			talking_core += 1; //off by one
			//printf("0 receives finish from %d\n", talking_core);
			int fer = fprintf(fp, "%d;%d;%f\n", (int)buf[talking_core][0], (int)buf[talking_core][1], buf[talking_core][2]);
			if (fer < 0) printf("Error writing!\n");
			jobdone += 1;
			if (jobsent < jobtotal) {
				vector<int> jobxy = joblist[jobsent];
				int my_job[2] = {jobxy[0], jobxy[1]};
				//printf("%d tells %d to do job %d %d with %d %d %d\n", 0, talking_core, my_job[0], my_job[1], jobsent, jobdone, jobtotal);
				MPI_Send(my_job, 2, MPI_INT, talking_core, tag, MPI_COMM_WORLD);
				MPI_Irecv(buf[talking_core], 3, MPI_DOUBLE, talking_core, tag, MPI_COMM_WORLD, &request[talking_core]);
				jobsent += 1;
			}
			if (jobdone % 10000 == 0) {
				t1 = clock();
				printf("%f Job %d out of %d done\n", ((float)t1)/CLOCKS_PER_SEC, jobdone, jobtotal);
			}
		}
		for (talking_core = 1; talking_core < CORE_TOTAL; talking_core++) {
			MPI_Send(exit_request, 2, MPI_INT, talking_core, tag, MPI_COMM_WORLD);
		}
		fclose(fp);
	}
	else { //servants
		string folder = string(d["DATA_LOC"]);
		int sinste[2] = {0, 0};
		int done = 0;
		int tag = 42;
		int ind_x, ind_y, ms, ns, dist;
		while (done == 0) {
			MPI_Status status;
			MPI_Recv(sinste, 2, MPI_INT, 0, tag, MPI_COMM_WORLD, &status);
			//printf("%d receives message %d %d from 0\n", CORE, sinste[0], sinste[1]);
			if (sinste[0] == -1) { //the shutdown signal
				done = 1;
				continue;
			}
			double my_dist = my_cellset.dist(sinste[0], sinste[1]);
			double reply[3] = {(double)sinste[0], (double)sinste[1], my_dist};
			//printf("%d replies to 0 with reply %f %f %f\n", CORE, reply[0], reply[1], reply[2]);
			MPI_Send(reply, 3, MPI_DOUBLE, 0, tag, MPI_COMM_WORLD);
		}
		//printf("core %d is done!\n", CORE);
	}
	
	MPI_Finalize();
	
	return 0;
}


