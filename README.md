# PriTL, a learning framework for probabilistic temporal logic specifications

PriTL is a tool that identifies the differences in Markov Chains using Probabilistic Temporal Logic. To this end, it implements the passive learning task of learning minimal probabilistic LTL separating two sets P and N of Markov Chains.

### Getting Started

PriTL requires [Python3.12+](https://www.python.org/downloads/), and some Python libaries. PriTL also requires the installation of [SPOT](https://spot.lre.epita.fr/) and [PRISM](https://www.prismmodelchecker.org/). Note that we have modified the PRISM source to suit our purposes, so we rely on a forked version of PRISM. We now give the steps of the installation process.

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
make -j$(sysctl -n hw.ncpu) && sudo make install
```

You also need to add SPOT Python Bindings to the Python path. One way to do this (for MacOS) is to run: 
```
export PYTHONPATH=~/.local/lib/python3.X/site-packages:$PYTHONPATH
```
where you replace X with python version

Please access and install from the forked version of PRISM
```
https://github.com/yashpote/prism
```
Then, follow the installation instructions as given in the README.md inside. Remember to add the prism binary to the path, e.g., as follows:
```
export PATH="$PATH:/Users/user/Desktop/prism/prism/bin"
```

### 3. Run PriTL
Use the following command to run PriTL with the desired parameters:
```bash
python3 main.py --experiment <experiment_type> --num_processes <num_processes> [--compile] [--run_all] [--nailgun]
```

### 4. Command-Line Arguments
- `--experiment` (`-e`): The type of experiment to run. Options:
  - `diff_tasks`: Learning from strategies generated from correct and incorrect tasks.
  - `same_task`: Learning from optimal and suboptimal strategies from the same task.
  - `variants`: Learning from variants of the probabilistic protocol EGL.
- `--num_processes` (`-p`): Number of processes to run in parallel (default: 1).
- `--compile` (`-c`): Compile the results into a CSV file (optional).
- `--run_all` (`-a`): Run all experiments (optional, computationally expensive).
- `--nailgun` (`-ng`): Use the Nailgun server for PRISM (optional, faster).
