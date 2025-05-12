import subprocess
import os
import json
import argparse
import time
import numpy as np
from multiprocessing import Pool
from separator import Separator, find_pltl_formula



def compile_results(folders):

    date_time = time.strftime("%d_%H_%M")
    all_results = []
    print(date_time)
    for folder in folders:
        all_files = os.listdir(folder)
        # starts with learn_info
        all_json_files = [os.path.join(folder, f) for f in all_files if f.startswith('learn_info')]
        for json_file in all_json_files:
            with open(json_file, 'r') as f:
                results = json.load(f)
                all_results.append(results)
        
    # write the results to a csv file with headers as the keys of the dictionary
    keys = all_results[0].keys()
    with open(f'results_{date_time}.csv', 'w') as f:
        f.write(','.join(keys)+'\n')
        for result in all_results:
            f.write(','.join([str(result[key]) for key in keys])+'\n')


def multi_process_run_ltl_learning(folders, num_examples, num_processes, prism_binary, atoms, labels):
    with Pool(processes=num_processes) as pool:
        args = [(folder, num, prism_binary, atoms, labels) for folder in folders for num in num_examples]
        pool.starmap(run_ltl_learning, args)

def run_ltl_learning(folder, num_examples, prism_binary, atoms, labels):

    # learning parameters
    max_size = 6
    delta = 0.05
    
    all_files = os.listdir(folder)
    
    all_positives = [os.path.join(folder, f) for f in all_files if f.startswith('pos')]
    all_negatives = [os.path.join(folder, f) for f in all_files if f.startswith('neg')]
    
    pos_files = all_positives[-num_examples:]
    neg_files = all_negatives[-num_examples:]
    total_examples = 2*num_examples

    info_file = f'learn_info_size_{max_size}_num_{total_examples}'
    
    find_pltl_formula(prism_binary=prism_binary, atoms=atoms, labels=labels, positive=pos_files, negative=neg_files, max_size=max_size, verbose=False, delta_param=delta, info_file=info_file)


def main():
    
    parser = argparse.ArgumentParser(description='The parameters for running the experiments')
    parser.add_argument('--experiment', '-e', type=str,default='variants')
    parser.add_argument('--num_processes', '-p', type=int, default=1)
    parser.add_argument('--compile', '-c', action='store_true',default=True)
    parser.add_argument('--run_all', '-a', action='store_true',default=False)
    parser.add_argument('--nailgun', '-ng', action='store_true',default=False)

    # Description of arguments:
    #
    # --experiment: the type of experiment to run, allows the following strings:
    # diff_tasks: learning from strategies generated from correct and incorrect tasks
    # same_task: learning from optimal and suboptimal strategies from the same task
    # variants: learning from variants of the probabilistic protocol EGL 
    # 
    # --num_processes: number of processes to run in parallel if multiprocessing is possible
    # 
    # --compile: whether to compile the results of the experiments (by default it is compiled in csv file with current date and time)# 
    # --run_all: whether to run all the experiments (computationally expensive) or just a subset (computatinally feasible)
    #
    # --nailgun: whether to use the nailgun server for PRISM (significantly faster)
    # Note: for nailgun, you need to activate the nailgun server first, which can be done as follows:
    # prism -ng &
    # If your Java version is >=19, you need to set a flag to allow this when you initially start PRISM:
    # PRISM_JAVA_PARAMS=-Djava.security.manager=allow prism -ng &

    args = parser.parse_args()
    experiment = args.experiment
    num_processes = args.num_processes
    compile = args.compile
    run_all = args.run_all
    nailgun = args.nailgun


    if nailgun:
        prism_binary = 'ngprism'
    else:
        prism_binary = 'prism'
    
    if experiment == 'diff_tasks':
        atoms = ['"a"', '"b"', '"h"']
        labels = ""
        if run_all:
            folders = [f'final_experiments/Strategies/application1/taskset{i}' for i in range(1, 6)]
            num_examples = [5,10]
            multi_process_run_ltl_learning(folders, num_examples, num_processes=num_processes, prism_binary=prism_binary, atoms=atoms, labels=labels)
        else:
            folders = [f'final_experiments/Strategies/application1/taskset{i}' for i in range(1, 4)]
            num_examples = [10]
            multi_process_run_ltl_learning(folders, num_examples, num_processes=num_processes, prism_binary=prism_binary, atoms=atoms, labels=labels)

    
    elif experiment == 'same_task':
        atoms = ['"a"', '"b"', '"h"']
        labels = ""
        if run_all:
            folders = [f'final_experiments/Strategies/application2/formula{i}' for i in range(1, 5)]
            num_examples = [5,10,15,20,25,30]
            multi_process_run_ltl_learning(folders, num_examples, num_processes=num_processes, prism_binary=prism_binary, atoms=atoms, labels=labels)
        else:
            folders = [f'final_experiments/Strategies/application2/formula{i}' for i in range(1, 4)]
            num_examples = [10,15]
            multi_process_run_ltl_learning(folders, num_examples, num_processes=num_processes, prism_binary=prism_binary, atoms=atoms, labels=labels)

    elif experiment == 'variants':
        
        atoms = []
        atoms_file = 'final_experiments/ModelVariants/atoms.txt'
        with open(atoms_file, 'r') as f:
            counter = 1
            labels = ""
            for line in f:
                if line == '---\n':
                    counter += 1
                    continue
                if counter == 1:
                    atoms.append(line.strip())
                elif counter == 2:
                    label_str = line.strip().split(':')
                    label_atom = label_str[0]
                    label_val = label_str[1]
                    labels += f"label {label_atom} = {label_val};\n"
        if run_all:
            folders = [f'final_experiments/ModelVariants/EGLP{i}' for i in range(1,8)]
            num_examples = [1]
            multi_process_run_ltl_learning(folders, num_examples, num_processes=num_processes, prism_binary=prism_binary, atoms=atoms, labels=labels)
        else:
            folders = [f'final_experiments/ModelVariants/EGLP{i}' for i in range(1,4)]
            num_examples = [1]
            multi_process_run_ltl_learning(folders, num_examples, num_processes=num_processes, prism_binary=prism_binary, atoms=atoms, labels=labels)
    else:
        print('Invalid experiment type')
        return
    
    if compile:
        compile_results(folders)


if __name__ == "__main__":
    
    main()
