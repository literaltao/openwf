## High Precision Open-World Website Fingerprinting

### Running code example

```
cd attacks
python Ha-kFP.py options
cd ../po
python conf-po.py options
```

(Code is generally in Python2, but it should be easily convertible to Python3 by fixing or just removing all the print functions.)

### Attacks

We place the code files for the attacks in the attacks/ folder. These attacks are all designed to output
the match function, and they all load parameters from an options file in order to run. 
The "notes" file in the folder explains how each attack is run.
We provide an "options" file in the folder as a sample.
Several cpp files need compiling.
Some attacks rely on libsvm, so we provided compiled versions of libsvm in the folder,
but they are likely not to work on other computers; the user may need to compile libsvm
themselves and put svm-train and svm-predict in the folder as we did.
(You need to first unzip the data for the attacks to run properly; see below.)

The options file determines which fold of the data it runs as training and testing
(gen_list() supports multiple ways to do this),
which implies that to do a full 10-fold test, you usually need to run the attack 10 times
using different options files (also vary CORE_NAME).
run-Pa-FeaturesSVM.py is an example of this.

### Data
We put some sample data, extracted from our real data, in precisebatch-small.zip.
Unzip the file to produce the precisebatch-small
This includes 100x10+1000 data points.
We cannot put the full data set in there due to size limitations;
our full data sets will be released on our maintained websites after publication.

### Precision Optimizers
We put PO code in the po/ folder. 
The POs directly read output files in attacks/output/ depending on an options file. 

conf-po.py is the confidence-based po; since it is designed to test out a variety
of K and M parameters, you will need to edit the code to choose the parameters you want 
(it is not read from options).

Distance calculations must first be done from the attacks/dist.cpp and attacks/dist-open.cpp files.
Then, run dist-process.py to process the distance files. (It will only process one type of attack at a time; check the code.)
Finally, run dist-tooclose.py and dist-toofar.py.
These last three files *do not* read options files, they were written for one-off use
for the full data set,
so they must be edited to be able to work for the smaller data set. 

Finally, the ensemble PO is in ensemble-short.py.
Similarly, some modifications are necessary for it to work on the sample data set.

We did not share all of the code we used in the paper; most of the rest of the code is fairly simple (e.g. sensitive client identification problem) and can be easily recreated from the description. We are nevertheless willing to share our other code if needed; contact us by e-mail. 

### Site lists and scripts

userscript-click.txt was used to load LINK1 and userscript-move.txt was used to load AJAX1.
LINK2 and AJAX2 were loaded with slightly modified versions of those two scripts by simply changing the parameters as described in the paper.

top-100-censor is the list of sensitive sites used to calculate r for the sensitive pages.
top-100 is the list of top 100 pages in both the monitored data set and to calculate r for the top pages. 
top-100-random is the list of random pages chosen from top 100,000 used to create the second monitored data set. 

top-10000-wiki is the list of non-monitored wiki pages.
top-100-wiki is the list of monitored wiki pages.



