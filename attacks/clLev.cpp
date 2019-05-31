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

//Uses mpi to output a lev file of pairwise distances between packet sequences
//Lev file should be processed by clgen-stratify to retrieve results

//Lu-Lev requires positive and negative packets to be calculated separately
//Two pairwise distances are computed, instead of one
//In older implementations, we output two files lev-pos and lev-neg
//For simplicity, we output only one file in this implementation
//We denote positive sequences as sites 0-CLOSED_SITENUM, and negative ones as sites CLOSED_SITENUM+1 to 2 * CLOSED_SITENUM + 2. 

#define UNIT 512
#define INCREMENT 600

typedef struct _cord{
	int x;
	int y;
}CORD;

typedef int TRACE;

int CLOSED_SITENUM, CLOSED_INSTNUM, OPEN_INSTNUM, CORE, CORE_TOTAL, TOTAL_NUM, degree;
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

class Levenshtein{

public:
	vector<int> buffer;
	vector<int> sizes;
	vector<TRACE*> pool;
	TRACE* str1;
	TRACE* str2;
	int method;

public:
	Levenshtein(string folder, int metr);
	~Levenshtein();
	CORD inverse_cantor(int z);
	
	int Parse_data(char* fname, int method);
	TRACE* fetch_pool(int index);
	double DLdis(int ms, int ns);
	double adjDLdis(int ms, int ns);
	double minimum(double a, double b, double c);

	int DLdel(int ms, int ns, int delele);
	double newDLdis(int ms, int ns);
};


Levenshtein :: Levenshtein(string folder, int metr){
	
	pool.clear();
	buffer.clear();
	sizes.clear();
	str1 = str2 = NULL;

	method = metr;

	char fname[200];
	
	for(int web = 0; web < CLOSED_SITENUM; web++){
		for(int trial = 0; trial < CLOSED_INSTNUM; trial++){
			memset(fname, 0, 200);
			sprintf(fname,"%s%d-%d.cell", folder.c_str(),web,trial);
			Parse_data(fname, method);
		}
	}
	for(int trial = 0; trial < OPEN_INSTNUM; trial++){
		memset(fname, 0, 200);
		sprintf(fname,"%s%d.cell", folder.c_str(),trial);
		Parse_data(fname, method);
	}

	if (method == 0) {//LuLev needs to load data twice, one for all positive packets in each paacket sequence, and one for negative
		for(int web = 0; web < CLOSED_SITENUM; web++){
			for(int trial = 0; trial < CLOSED_INSTNUM; trial++){
				memset(fname, 0, 200);
				sprintf(fname,"%s%d-%d.cell", folder.c_str(),web,trial);
				Parse_data(fname, -1);
			}
		}
		for(int trial = 0; trial < OPEN_INSTNUM; trial++){
			memset(fname, 0, 200);
			sprintf(fname,"%s%d.cell", folder.c_str(),trial);
			Parse_data(fname, -1);
		}
	}

	cout<<"constructor finished, size of pool is: "<<pool.size()<<endl;
}

Levenshtein :: ~Levenshtein(){
	for(int i = 0; i < pool.size();i++)
		delete[] pool.at(i);
}

TRACE* Levenshtein::fetch_pool(int index){
	if(index >= pool.size()){
		printf("fetch_pool error [index=%d poolsize=%lu]", index, pool.size());
		exit(1);
	}
	return pool.at(index);
}


int Levenshtein::Parse_data(char *fname, int method){
	//method 0 is for positive packets for LuLev, and method -1 is for negative packets
	//other ones are normal
	FILE* fp = NULL;
	int length,size;
	float time;
	int i, round;
	
	buffer.clear();
	buffer.push_back(0);

	fp = fopen(fname, "r");
	if(!fp){
		cout<<fname<<"  cannot open!" <<endl;
		exit(1);
	}
	
	int count = 0;	
	while(!feof(fp) && count < 5000){
		if(0 > fscanf(fp,"%f\t%d",&time, &length))
			continue;
		if (method == 0) { //LuLev, positive
			if (length >= 0) {
			length = length/abs(length); 
			buffer.push_back(length);
			count++;
			}
		}
		else if (method == -1) { //LuLev, negative
			if (length < 0) {
			length = length/abs(length); 
			buffer.push_back(length);
			count++;
			}
		}
		else { //other algorithms, take both
			length = length/abs(length);
			buffer.push_back(length);
			count++;
		}
	}
	
	fclose(fp);

	TRACE* tmp = new TRACE[buffer.size()];
	for(int x = 0; x < buffer.size(); x++)
		tmp[x] = buffer.at(x);
	pool.push_back(tmp);
	sizes.push_back(buffer.size());
	return 0;
}

int contains(int* str1, int element, int len) {
	int toret = -1;
	for (int i = 0; i < len; i++) {
		if (str1[i] == element)
			toret = i;
	}
	return toret;
}

double Levenshtein::adjDLdis(int ms, int ns){

//method 0: Lu-Lev
//method 1: Ca-OSAD
//method 2: Wa-OSAD
//method 3: Wa-FLev (handled ny newDLdis)
//method 4: Wa-OSAD, but only disabling substitution
//method 5: Wa-OSAD, but only increasing outgoing cost
//method 6: Wa-OSAD, but only changing transcost

	double ret = 0;
	int min;

	int m = ms;
	int n = ns;
	min = m < n ? m : n;
	min = min == 0 ? 1 : min;

	float adj = 1;
	if (m >= 500 and n >= 500) { 
		m = 500;
		n = 500;
		adj = ms < ns ? ns/float(ms) : ms/float(ns);
	}

	int i,j;
    	float subcost,transcost;

	float** dis = new float*[m];
	for(i=0;i<m;i++)
		dis[i]= new float[n];

	int maxpacket = 0;
	int minpacket = 0;

	for (int k = 0; k < 2; k++) {
		int* pt;
		int len;
		if (k == 0) {
			pt = str1;
			len = m;
		}
		if (k == 1) {
			pt = str2;
			len = n;
		}
		for (i = 0; i < len; i++) {
			if (pt[i] > maxpacket)
				maxpacket = pt[i];
			if (pt[i] < minpacket)
				minpacket = pt[i];
		}
	}
	
	for(i=0; i<m; i++)
		dis[i][0]=i*2;
	for(j=0; j<n; j++)
		dis[0][j]=j*2;
	
	int db, x1, y1 = 0;
	float P = 0;

	float idcost[2] = {2, 2};
	
	if (method == 2)
		idcost[0] = 6;
	if (method == 5) {
		idcost[0] = degree * 10 + 2; //2 to 12
	}
	
	if (method == 2 or method == 4 or method == 5 or method == 6)
		subcost = 20;
	else
		subcost = 2;

	if (method == 1)
		transcost = 0.1;

	if (method == 0) //Lu-Lev doesn't allow transpositions
		transcost = 100;
	

	for(i=1; i<m; i++){
		db = 0;
		for(j=1; j<n; j++){
			if (method == 2) {
				P = (float)i/m > (float)j/n ? (float)j/n : (float)i/m;
				transcost = (1-P*0.9) * (1-P*0.9); //goes from 1 to 0.01;
			}
			if (method == 6) {
				P = (float)i/m > (float)j/n ? (float)j/n : (float)i/m;
				transcost = 1;
				for (int d = 0; d < (int)degree; d++) {
					transcost *= (1-P*0.9);
				}
	//			transcost = pow((1-P*0.9), degree * 10 + 0.1);
			}
			//printf("%d %d %d %d %d\n", METRIC, i, j, x1, y1);
			if (str1[i] == str2[j]) {
				dis[i][j] = minimum (
					dis[i-1][j] + idcost[(str1[i] > 0 ? 0 : 1)], //abs(str1[i]),  // a deletion
        	        		dis[i][j-1] + idcost[(str2[j] > 0 ? 0 : 1)], //abs(str2[j]),  // an insertion
        	        		dis[i-1][j-1] // a substitution
				);
				db = j;
			}
			else {
				dis[i][j] = minimum (
					dis[i-1][j] + idcost[(str1[i] > 0 ? 0 : 1)], //abs(str1[i]),  // a deletion
        	 	       		dis[i][j-1] + idcost[(str2[j] > 0 ? 0 : 1)], //abs(str2[j]),  // an insertion
        		        	dis[i-1][j-1] + subcost // a substitution
				);
				if(i > 1 && j > 1 && str1[i] == str2[j-1] && str1[i-1] == str2[j]) {
					dis[i][j] = 	dis[i][j] < dis[i-2][j-2] + transcost ? 
							dis[i][j] : dis[i-2][j-2] + transcost;
				}
			}
			//printf("%d %d %d %d \n", i, j, dis[i][j], dis);
		}
	}
	ret = dis[m-1][n-1] * adj /min;

	for(i = 0 ; i < m; i++) {
		delete[] dis[i];
	}
	delete[] dis;

	return ret;
}

double Levenshtein::DLdis(int ms, int ns){

//method 0: Lu-Lev
//method 1: Ca-OSAD
//method 2: Wa-OSAD
//method 3: Wa-FLev (handled ny newDLdis)
//method 4: Wa-OSAD, but only disabling substitution
//method 5: Wa-OSAD, but only increasing outgoing cost
//method 6: Wa-OSAD, but only changing transcost

	double ret = 0;
	int min;

	int m = ms;
	int n = ns;
	min = m < n ? m : n;
	min = min == 0 ? 1 : min;

	int i,j;
    	float subcost,transcost;

	float** dis = new float*[m];
	for(i=0;i<m;i++)
		dis[i]= new float[n];

	int maxpacket = 0;
	int minpacket = 0;

	for (int k = 0; k < 2; k++) {
		int* pt;
		int len;
		if (k == 0) {
			pt = str1;
			len = m;
		}
		if (k == 1) {
			pt = str2;
			len = n;
		}
		for (i = 0; i < len; i++) {
			if (pt[i] > maxpacket)
				maxpacket = pt[i];
			if (pt[i] < minpacket)
				minpacket = pt[i];
		}
	}
	
	for(i=0; i<m; i++)
		dis[i][0]=i*2;
	for(j=0; j<n; j++)
		dis[0][j]=j*2;
	
	int db, x1, y1 = 0;
	float P = 0;

	float idcost[2] = {2, 2};
	
	if (method == 2)
		idcost[0] = 6;
	if (method == 5) {
		idcost[0] = degree * 10 + 2; //2 to 12
	}
	
	if (method == 2 or method == 4 or method == 5 or method == 6)
		subcost = 20;
	else
		subcost = 2;

	if (method == 1)
		transcost = 0.1;

	if (method == 0) //Lu-Lev doesn't allow transpositions
		transcost = 100;
	

	for(i=1; i<m; i++){
		db = 0;
		for(j=1; j<n; j++){
			if (method == 2) {
				P = (float)i/m > (float)j/n ? (float)j/n : (float)i/m;
				transcost = (1-P*0.9) * (1-P*0.9); //goes from 1 to 0.01;
			}
			if (method == 6) {
				P = (float)i/m > (float)j/n ? (float)j/n : (float)i/m;
				transcost = 1;
				for (int d = 0; d < (int)degree; d++) {
					transcost *= (1-P*0.9);
				}
	//			transcost = pow((1-P*0.9), degree * 10 + 0.1);
			}
			//printf("%d %d %d %d %d\n", METRIC, i, j, x1, y1);
			if (str1[i] == str2[j]) {
				dis[i][j] = minimum (
					dis[i-1][j] + idcost[(str1[i] > 0 ? 0 : 1)], //abs(str1[i]),  // a deletion
        	        		dis[i][j-1] + idcost[(str2[j] > 0 ? 0 : 1)], //abs(str2[j]),  // an insertion
        	        		dis[i-1][j-1] // a substitution
				);
				db = j;
			}
			else {
				dis[i][j] = minimum (
					dis[i-1][j] + idcost[(str1[i] > 0 ? 0 : 1)], //abs(str1[i]),  // a deletion
        	 	       		dis[i][j-1] + idcost[(str2[j] > 0 ? 0 : 1)], //abs(str2[j]),  // an insertion
        		        	dis[i-1][j-1] + subcost // a substitution
				);
				if(i > 1 && j > 1 && str1[i] == str2[j-1] && str1[i-1] == str2[j]) {
					dis[i][j] = 	dis[i][j] < dis[i-2][j-2] + transcost ? 
							dis[i][j] : dis[i-2][j-2] + transcost;
				}
			}
			//printf("%d %d %d %d \n", i, j, dis[i][j], dis);
		}
	}
	ret = dis[m-1][n-1]/min;

	for(i = 0 ; i < m; i++) {
		delete[] dis[i];
	}
	delete[] dis;

	return ret;
}

int abs(int k) {
	if (k > 0)
		return k;
	else
		return -k;
}

double Levenshtein::newDLdis(int ms, int ns) {
	//from transcost = 0.01, 0.02, 0.03 x posdelcost = 2, 4, 6, 4 * 0.01 is the best
//	double transcost = (1+(METRIC))*0.001;
	double transcost = 0.01;
	double posdelcost = 4;
	double negdelcost = 1;
	int i = 0;
	int poscount = 0;
	int negcount = 0;
	int min = 0;

	min = ms < ns ? ms : ns;
	min = min == 0 ? 1 : min;

	for (i = 0; i < ms; i++) {
		if (str1[i] > 0)
			poscount += 1;
		else
			negcount += 1;
	}
	
	for (i = 0; i < ns; i++) {
		if (str2[i] > 0)
			poscount += 1;
		else
			negcount += 1;
	}

	if (ns == 0) {
		return 0;
	}
	int* dicn = new int[ms]; //dictionary of all elements in str1
	int dicnlen = 0; //true size of dictionary; saves memory. 
	for (i = 0; i < ms; i++) {
		int a = contains(dicn, str1[i], dicnlen);
		if (a == -1) {
			dicn[dicnlen] = str1[i];
			dicnlen += 1;
		}
	}

	int** dicncount = new int*[dicnlen]; //location of all elements in str1
	int* dicncountlen = new int[dicnlen];
	int* dicncountlentemp = new int[dicnlen];
	int count = 0;
	int dist = 0;

	for (i = 0; i < dicnlen; i++) {
		dicncount[i] = new int[ms];
		dicncountlen[i] = 0;
	}
	for (i = 0; i < ms; i++) {
		int a = contains(dicn, str1[i], dicnlen);
		dicncount[a][dicncountlen[a]] = i;
		dicncountlen[a] += 1;
	}
	for (i = 0; i < dicnlen; i++) {
		dicncountlentemp[i] = dicncountlen[i];
	}


	for (i = 0; i < ns; i++) {
		int a = contains(dicn, str2[i], dicnlen);
		if (a != -1) {
			count = dicncountlen[a] - dicncountlentemp[a];
			if (count < dicncountlen[a]) {
				if (str2[i] > 0)
					dist += (dicncount[a][count] - i > 0)? dicncount[a][count] - i : i - dicncount[a][count];
				dicncountlentemp[a] -= 1;
				if (str2[i] > 0)
					poscount -= 1;
				else
					negcount -= 1;
			}
		}
	}

	double cost = poscount * posdelcost + negcount * negdelcost + dist * transcost;

	for (int i = 0; i < dicnlen; i++) {
		delete[] dicncount[i];
	}

	delete[] dicncount;
	delete[] dicn;
	delete[] dicncountlen;
	delete[] dicncountlentemp;

	return cost/min;

}

double Levenshtein::minimum(double a, double b, double c){
	double min = a;
	if(b < min)
		min = b;
	if(c < min)
		min = c;

	return min;
}

CORD Levenshtein::inverse_cantor(int z){
	CORD ret;
	int w = floor((sqrt(8.0*z+1)-1)/2);
	int t = (w*w+w)/2;
	ret.y = z-t;
	ret.x = w-ret.y;

	return ret;
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

string itoa(int val) {
	string ret;
	ostringstream converter;
	converter << val;
	ret = converter.str();
	return ret;
}
void ind_to_sinste(int a, int& s, int& i) {
	//converts integer a (of TOTAL_NUM) to site and inst
	if (a < CLOSED_SITENUM * CLOSED_INSTNUM){
		s = a/CLOSED_INSTNUM;
		i = a%CLOSED_INSTNUM;	
	}
	else {
		s = CLOSED_SITENUM;
		i = a - CLOSED_SITENUM * CLOSED_INSTNUM;
	}}

int main(int argc, char** argv){
//

	if(argc != 2){
	    cout <<"call: ./clLev <option name>"<<endl;
	    cout << "example: ./clLev options-classify-100x100" << endl;
		cout << "method 0 = Lu-Lev, method 1 = Ca-OSAD, method 2 = Wa-OSAD, method 3 = Wa-FLev" << endl;
	    exit(1);
	}

	MPI_Init(&argc, &argv);
	MPI_Comm_rank(MPI_COMM_WORLD, &CORE);
	MPI_Comm_size(MPI_COMM_WORLD, &CORE_TOTAL);
	printf("this core=%d total cores=%d\n", CORE, CORE_TOTAL);

	char* optionname = argv[1];
	
	read_options(string(optionname));

	//we explicitly define those for convenience:
	CLOSED_SITENUM = atoi(d["CLOSED_SITENUM"].c_str());
	CLOSED_INSTNUM = atoi(d["CLOSED_INSTNUM"].c_str());
	OPEN_INSTNUM = atoi(d["OPEN_INSTNUM"].c_str());
	TOTAL_NUM = CLOSED_SITENUM * CLOSED_INSTNUM + OPEN_INSTNUM;

	FILE *fp = NULL;
	string fname;
	printf("%d %d %d %d\n", CLOSED_SITENUM, CLOSED_INSTNUM, OPEN_INSTNUM, TOTAL_NUM);
	//if I am the master, check output file and load it:
	if (CORE == 0) {
		vector<vector<int> > joblist;
		int inum, inum2;
//		for (int s = 0; s < 1; s++) {
		for (int a = 0; a < TOTAL_NUM; a++) {
			for (int b = a+1; b < TOTAL_NUM; b++) {
				int s, i, s2, i2;
				ind_to_sinste(a, s, i);
				ind_to_sinste(b, s2, i2);
				int job_i[] = {s, i, s2, i2};
				vector<int> job (job_i, job_i + sizeof(job_i)/sizeof(int));
				joblist.push_back(job);
				if (d["LEV_METHOD"] == "0") { //for Lu-Lev
					int job_i2[] = {s + CLOSED_SITENUM + 1, i, s2 + CLOSED_SITENUM + 1, i2};
					vector<int> job2 (job_i2, job_i2 + sizeof(job_i2)/sizeof(int));
					joblist.push_back(job2);
				}
			}
		}
		fname = d["OUTPUT_LOC"] + "clLev-" + d["LEV_METHOD"] + ".lev";
		fp = fopen(fname.c_str(), "r");
		string fnameout;
		fnameout = fname + ".bak";
		FILE * fout = fopen(fnameout.c_str(), "w");
		/*if(fp){
			printf("Input file %s found, loading from input file\n", fname.c_str());
			int s, i, s2, i2;
			char * garb = new char[500];
			while (fscanf(fp, "%d;%d;%d;%d;%s\n", &s,&i,&s2,&i2,garb) == 5) {
				int job_i[] = {s, i, s2, i2};
				vector<int> job (job_i, job_i + sizeof(job_i)/sizeof(int));
				vector<vector<int> >::iterator it;
				it = find(joblist.begin(), joblist.end(), job);
				int index = distance(joblist.begin(), it);
				if (index < joblist.end() - joblist.begin()) {
					joblist.erase(joblist.begin()+index);
					fprintf(fout, "%d;%d;%d;%d;%s\n",s,i,s2,i2,garb);
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
		printf("Job list has length %d, now initiating\n", (int)joblist.size());

		int jobsent = 0; //number of jobs sent by master
		int jobdone = 0; //number of jobs completed and received from servants
		int jobtotal = (int)joblist.size();
		fp = fopen(fname.c_str(), "a+");
		if(!fp){
			cout<<"cannot open file " << fname << endl;
			exit(1);
		}

		//int web_x, trial_x, web_y, trial_y, ind_x, ind_y;
		//int ms, ns;

		 //* status;
		//status = new MPI_Status[CORE_TOTAL]; //0 is master
		MPI_Request * request;
		request = new MPI_Request[CORE_TOTAL];
		int ** buf;
		buf = new int*[CORE_TOTAL];
		for (int i = 0; i < CORE_TOTAL; i++) {
			buf[i] = new int[7];
		}
		int tag = 42;
		int talking_core = 1;
		int exit_request[4] = {-1, -1, -1, -1};
		int waiting_cores = 0; //normally equals CORE_TOTAL-1, but in edge cases might be smaller

		for (talking_core = 1; talking_core < CORE_TOTAL; talking_core++) {
			if (jobsent < jobtotal) {
				int my_job[4] = {joblist[jobsent][0], joblist[jobsent][1],
						joblist[jobsent][2], joblist[jobsent][3]};
				//printf("%d tells %d to do job %d %d %d %d\n", 0, talking_core, my_job[0], my_job[1], my_job[2], my_job[3]);
				MPI_Send(my_job, 4, MPI_INT, talking_core, tag, MPI_COMM_WORLD);
				MPI_Irecv(buf[talking_core], 7, MPI_INT, talking_core, tag, MPI_COMM_WORLD, &request[talking_core]);
				jobsent += 1;
				waiting_cores += 1;
			}
			else MPI_Send(exit_request, 4, MPI_INT, talking_core, tag, MPI_COMM_WORLD);
		}
		
		//printf("0 has sent all requests, now waiting for replies\n");

		clock_t t1;
		while (jobdone < jobtotal) {
			MPI_Status status;
			int talking_core;
			MPI_Waitany(waiting_cores, &request[1], &talking_core, &status);
			talking_core += 1; //off by one
			//printf("0 receives finish from %d\n", talking_core);
			//printf("%d %d\n", buf[1][4], buf[1][6]);
			fprintf(fp, "%d;%d;%d;%d;%d;%d;%d\n", buf[talking_core][0], buf[talking_core][1], buf[talking_core][2], buf[talking_core][3],
			buf[talking_core][4], buf[talking_core][5], buf[talking_core][6]);
			jobdone += 1;
			if (jobsent < jobtotal) {
				int my_job[4]  = {joblist[jobsent][0], joblist[jobsent][1],
						joblist[jobsent][2], joblist[jobsent][3]};
				MPI_Send(my_job, 4, MPI_INT, talking_core, tag, MPI_COMM_WORLD);
				MPI_Irecv(buf[talking_core], 7, MPI_INT, talking_core, tag, MPI_COMM_WORLD, &request[talking_core]);
				jobsent += 1;
			}
			else MPI_Send(exit_request, 4, MPI_INT, talking_core, tag, MPI_COMM_WORLD);
			if (jobdone % 100 == 0) {
				t1 = clock();
				printf("%f Job %d out of %d done\n", ((float)t1)/CLOCKS_PER_SEC, jobdone, jobtotal);
			}
		}
		
	}
	else { //servants
		string folder = string(d["DATA_LOC"]);
		Levenshtein Lclass(folder, atoi(d["LEV_METHOD"].c_str()));
		int sinste[4] = {0, 0, 0, 0};
		int done = 0;
		int tag = 42;
		int ind_x, ind_y, ms, ns, dist;
		while (done == 0) {
			MPI_Status status;
			MPI_Recv(sinste, 4, MPI_INT, 0, tag, MPI_COMM_WORLD, &status);
			//printf("%d receives message %d %d %d %d from 0\n", CORE, sinste[0], sinste[1], sinste[2], sinste[3]);
			if (sinste[0] == -1) { //the shutdown signal
				done = 1;
				continue;
			}
			ind_x = sinste_to_ind(sinste[0], sinste[1]);
			ind_y = sinste_to_ind(sinste[2], sinste[3]);
			//printf("fetch_pool: ind %d sinste %d sinste %d ind %d sinste %d sinste %d\n", ind_x, sinste[0], sinste[1], ind_y, sinste[2], sinste[3]);
			Lclass.str1 = Lclass.fetch_pool(ind_x);
			Lclass.str2 = Lclass.fetch_pool(ind_y);
			ms = Lclass.sizes.at(ind_x);
			ns = Lclass.sizes.at(ind_y);
			dist = (int) (Lclass.DLdis(ms, ns)*1000000);
			int reply[7] = {sinste[0], sinste[1], sinste[2], sinste[3], ms, ns, dist};
			//printf("%d replies to 0 with reply %d %d %d %d %d %d %d\n", CORE, reply[0], reply[1], reply[2], reply[3], reply[4], reply[5], reply[6]);
			MPI_Send(reply, 7, MPI_INT, 0, tag, MPI_COMM_WORLD);
		}
		//printf("core %d is done!\n", CORE);
	}
	
	MPI_Finalize();
	
	return 0;
}


