# PriTL, a learning framework for probabilistic temporal logic specifications

PriTL is a tool that identifies the differences in Markov Chains using Probabilistic Temporal Logic. To this end, it implements the passive learning task of learning minimal probabilistic LTL separating two sets P and N of Markov Chains.

### Getting Started

PriTL requires [Python3.12+](https://www.python.org/downloads/), and some Python libaries. PriTL also requires the installation of [SPOT](https://spot.lre.epita.fr/) and [PRISM](https://www.prismmodelchecker.org/). Note that we have modified the PRISM source to suit our purposes, so we provide our customized version along with the supplementary material.

Start by creating a virtual environment and installing the required python libraries
```
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

To install SPOT, first download the SPOT compressed repository from their website, and then follow: 
```
tar -xvzf spot-x.y.z.tar.gz
cd spot-x.y.z
./configure --prefix=$(python -c "import sys; print(sys.prefix)") --with-python
make -j$(sysctl -n hw.ncpu) && make install
```

You also need to add SPOT Python Bindings to the Python path. One way to do this (for MacOS) is to run: 
```
export PYTHONPATH=/opt/homebrew/lib/python3.X/site-packages/:$PYTHONPATH
```

To install PRISM, first unzip prism-master.zip. Then, follow the installation instructions as given in the README.md inside. Remember to add the prism binary to the path, e.g., as follows:
```
export PATH="$PATH:/Users/user/Desktop/prism/prism/bin"
```

### Running PriTL

To run experiments with the default parameters presented in the paper, use the command:
```
python3 main.py 
```
