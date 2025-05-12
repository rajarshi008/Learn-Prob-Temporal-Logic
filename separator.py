import os
import subprocess
from gen_logics import GrammarGenPLTL
from boolcomb import Boolcomb
import numpy as np
import time
import json
import heapq as hq


PRQUERY = "=?"

class Separator:
    '''
    Class that implements the probabilistic threshold search (PTS) procedure: (i) performs model checking and (ii) consistency checking
    '''
    def __init__(self, positive, negative, verbose, delta, bsc, prism_binary='prism', formula_type='.pltl', only_minimal=True, only_greater=True, only_smaller=False):
        
        self.prism_binary = prism_binary
        self.positive = positive
        self.negative = negative
        self.verbose = verbose
        self.delta = delta
        self.answer_file = 'answer' + formula_type
        self.all_results = {}
        self.prism_flags = ['--maxiters', '1000000', '--exportvector', 'stdout']

        self.max_diff = 0
        self.max_diff_formula = None

        self.discard_counter = 0
        self.only_minimal = only_minimal
        self.only_greater = only_greater
        self.only_smaller = only_smaller
        self.bsc = bsc

        self.separation_time = 0
        self.PRISM_time = 0

    def generate_probs(self, tl_file, formula_size):
        '''
        Function that generates the probability thresholds for each model
        '''
        self.formula_size = formula_size
        self.results = {}
        self.discards = {}
        prism_runtime = 0

        for pos in self.positive:
            t0 = time.time()
            output_dict = self.run_prism(pos, tl_file)
            prism_runtime += time.time() - t0
            for formula in output_dict:
                if formula not in self.results:
                    self.results[formula] = [np.array([]), np.array([])]
                    self.discards[formula] = [np.array([]), np.array([])]
                self.results[formula][0] = np.append(self.results[formula][0], output_dict[formula][0])

                # discarding heursitics
                if np.all(output_dict[formula] == 1):
                    self.discards[formula][0] = np.append(self.discards[formula][0], 1)
                elif np.all(output_dict[formula] == 0):
                    self.discards[formula][0] = np.append(self.discards[formula][0], 0)
                else:
                    self.discards[formula][0] = np.append(self.discards[formula][0], -1)

        for neg in self.negative:
            t0 = time.time()
            output_dict = self.run_prism(neg, tl_file)
            prism_runtime += time.time() - t0
            for formula in output_dict:
                self.results[formula][1] = np.append(self.results[formula][1], output_dict[formula][0])
                
                # discarding heursitics
                if np.all(output_dict[formula] == 1):
                    self.discards[formula][0] = np.append(self.discards[formula][0], 1)
                elif np.all(output_dict[formula] == 0):
                    self.discards[formula][0] = np.append(self.discards[formula][0], 0)
                else:
                    self.discards[formula][0] = np.append(self.discards[formula][0], -1)

        formula_list = list(self.results.keys())
        discard_index = []
        for i in range(len(formula_list)):
            formula = formula_list[i]

            # discard condition
            discard_cond = np.all(self.discards[formula][0] == 1) and np.all(self.discards[formula][0] == 1) or np.all(self.discards[formula][0] == 0) and np.all(self.discards[formula][0] == 0)
            if discard_cond:
                self.discard_counter += 1
                discard_index.append(i)
            else:
                #calculate score for the formula
                if np.all(self.results[formula][0]==0) or np.all(self.results[formula][1]==1):
                    continue
                score_formula = self.bsc.score(formula, formula_size[0], self.results[formula])
                self.bsc.size[formula] = formula_size[0]
                hq.heappush(self.bsc.heap, (-score_formula, formula))
        
        checking_time = time.time()
        check = self.check_separation()
        checking_time = time.time() - checking_time

        self.separation_time += checking_time
        self.PRISM_time += prism_runtime

        return check, discard_index

    def check_separation(self):
        '''
        Checks if the formulas are separating the positive and negative examples with the computed thresholds
        '''
        answers = []
        for formula in self.results:
            
            
            result_formula = None
            pos_results = self.results[formula][0]
            neg_results = self.results[formula][1]
            
            max_pos = max(pos_results)
            min_neg = min(neg_results)
            min_pos = min(pos_results)
            max_neg = max(neg_results)
            
            if self.only_smaller:
                if max_pos < min_neg and min_neg - max_pos > self.delta:
                    mid_val = round((min_neg+max_pos)/2,5)
                    if mid_val >= 0.5:
                        continue
                    result_formula = formula.replace(PRQUERY, '<'+str(round((min_neg+max_pos)/2,5)))
                    answers.append(result_formula)
                    if min_neg - max_pos > self.max_diff:
                        self.max_diff = min_neg - max_pos
                        self.max_diff_formula = result_formula
            if self.only_greater:
                
                if min_pos > max_neg and min_pos - max_neg > self.delta:
                    mid_val = round((min_pos+max_neg)/2,5)
                    if min_pos < 0.8:
                        continue
                    result_formula = formula.replace(PRQUERY, '>'+str(mid_val))
                    answers.append(result_formula)
                    if min_pos - max_neg > self.max_diff:
                        self.max_diff = min_pos - max_neg
                        self.max_diff_formula = result_formula

        if answers != []:
            self.all_results.update({self.formula_size: answers})
            with open(self.answer_file, 'a+') as f:
                for answer in answers:
                    f.write(answer+'\n')
            return True
        else:
            return False

    def run_prism(self, pm_file, tl_file):
        '''
        Function that runs PRISM on a given DTMC file
        '''
        tl_folder = os.path.dirname(tl_file)
        logging_file = tl_folder+'/log-check.log'
        command = [self.prism_binary, pm_file, tl_file] + self.prism_flags + ['--mainlog', logging_file]
        try:
            proc = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            proc.wait()
            #result = proc.communicate()[0].decode('utf-8')
            
            #print(result)
            #with open('output.txt', 'w') as f:
            #    f.write(result)

            with open(logging_file, 'r') as f:
                result = f.read()
            
            #print(result)
            os.remove(logging_file)
            output_dict = self.extract_results(result)
            return output_dict
        except subprocess.CalledProcessError as e:
            print(f"Error running PRISM on {pm_file}: {e}")
            return None

    def extract_results(self, text):
        '''
        Function that parses the PRISM output
        '''
        output_dict = {}
        if "\n0 properties" in text or text == "":
            print('No properties found')
            return []
        all_outputs = text.split('---------------------------------------------------------------------\n')[1:]
        #print(len(all_outputs))
        for output in all_outputs:
            output_list = output.split('\n\n')
            formula = output_list[0].strip()
            #print(formula)
            if formula == '':
                continue
            for i in range(len(output_list)):
                s = output_list[i]
                #print(s)
                if 'Result' in s:
                    if 'true' in s or 'false' in s:
                        formula_result = True if 'true' in s else False
                        vector_text = output_list[i+1]
                        if 'v = [\n' == vector_text[:6]:
                            formula_vector = np.array(list(map(bool,vector_text[6:-3].split('\n'))))
                        else:
                            raise ValueError('PRISM output is not parsed properly')
                    else:
                        formula_result = round(float(s.split(' ')[1]), 5)
                        vector_text = output_list[i+1]
                        if 'v = [\n' == vector_text[:6]:
                            formula_vector = np.array(list(map(float,vector_text[6:-3].split('\n'))))
                        else:
                            print(formula,vector_text[:10])
                            raise ValueError('PRISM output is not parsed properly')
            output_dict[formula] = formula_vector
        return output_dict

    def verify_formula(self):

        for pos in self.positive:
            output_dict = self.run_prism(pos, self.answer_file)
            
            for formula in output_dict:
                if not output_dict[formula]:
                    print('There is a problem in %s for file %s' % (formula, pos))
        
        for neg in self.negative:
            output_dict = self.run_prism(neg, self.answer_file)
            for formula in output_dict:
                if output_dict[formula]:
                    print('There is a problem in %s for file %s' % (formula, neg))

def find_pltl_formula(prism_binary, atoms, labels, positive, negative, max_size, verbose, delta_param=0.05, info_file='info'):
    '''
    Main function that combines all three procedures: GBE, PTS, and BSC
    '''
    max_depth = 2
    external_folder = '/'.join(positive[0].split('/')[:-1])

    # remove all the files and folders from the previous run
    if os.path.exists(f'{external_folder}/temp_{info_file}'):
        for file in os.listdir(f'{external_folder}/temp_{info_file}'):
            os.remove(os.path.join(f'{external_folder}/temp_{info_file}', file))
        os.rmdir(f'{external_folder}/temp_{info_file}')
    if os.path.exists(f'{external_folder}/answer_{info_file}.pltl'):
        os.remove(f'{external_folder}/answer_{info_file}.pltl')

    #create a temporary folder to store the pltl files
    folder = f'{external_folder}/temp_{info_file}'
    if not os.path.exists(folder):
        os.makedirs(folder)
    print(f"Folder created at {folder}")
    
    # Starting the three procedures
    grammar = GrammarGenPLTL(atoms, max_depth, max_size)
    bsc = Boolcomb(max_size=max_size, max_initial_set=5, delta=delta_param)
    sep = Separator(prism_binary=prism_binary, positive=positive, negative=negative, verbose=verbose, delta=delta_param, bsc=bsc)
    
    # Initialize GBE
    grammar.heuristics['discard_heur'] = True
    grammar.heuristics_counter['discard_heur'] = 0
    grammar.heuristics_times['discard_heur'] = 0
    grammar.init_formulas()
    
    found_minimal = False
    found_pts = False
    found_bsc = False

    file_path = os.path.join(folder, f'temp_{1}_{0}.pltl')
    print(f"#### Checking for size {1} and depth {0}")
    with open(file_path, 'w') as f:
        if labels:
            f.write(labels)
        for formula in grammar.formula_list[(0,1)]:
            f.write("P=? [ " + formula.prettyPrint() + " ]\n")
            

    formula_listformat = list(grammar.formula_list[(0,1)])
    found, discard_index = sep.generate_probs(file_path, (1,0))
    if found:
        print("Status: Found separating formula")
    else:
        print("Status: No separating formula found for this size and depth")

    if sep.only_minimal and sep.all_results != {}:
        print(sep.all_results)
        return
    
    if grammar.heuristics['discard_heur']:
        for index in discard_index:
            grammar.formula_list[(0,1)].discard(formula_listformat[index])
            grammar.heuristics_counter['discard_heur'] += 1
    
    # Start the main search over formulas of different sizes and depths
    for size in range(2, max_size + 1):
        grammar.gen_next_size()
        for depth in range(max_depth+1):
            if grammar.formula_list[(depth,size)]:
                print(f"#### Checking for size {size} and depth {depth}")
                formula_listformat = list(grammar.formula_list[(depth,size)])
                file_path = os.path.join(folder, f'temp_{size}_{depth}.pltl')
                with open(file_path, 'w') as f:
                    if labels:
                        f.write(labels)
                    for formula in grammar.formula_list[(depth,size)]:
                        f.write("P=? [ " + formula.prettyPrint() + "]\n")
                
                found, discard_index = sep.generate_probs(file_path, (size, depth))
                if found:
                    found_minimal = True
                    found_pts = True
                    print("Status: Found separating formula using PTS")
                    print(sep.all_results)
                else:
                    if not found_bsc:
                        found_bsc = bsc.search()
                    if found_bsc:
                        print("Status: Found separating formula using BSC")
                        print(bsc.all_results)
                        
                    else:
                        print("Status: No separating formula found for this size and depth")

                if sep.only_minimal and found_minimal:
                    break
                
                if grammar.heuristics['discard_heur']:
                    for index in discard_index:
                        grammar.formula_list[(depth,size)].discard(formula_listformat[index])
                        grammar.heuristics_counter['discard_heur'] += 1

        if found_bsc and bsc.found_size == size+1 and sep.only_minimal:
            found_minimal = True
            break

        if sep.only_minimal and found_minimal:
            break
    
    # Printing and storing the results
    print("Here are all the formulas")
    all_formulas = []
    min_done = False
    minimal_formulas = []
    if found_minimal:
        
        if found_pts:
            print("Found through probability threshold search")
            for key, value in sep.all_results.items():
                print(f"Size: {key[0]}, Depth: {key[1]}")
                counter = 0
                for formula in value:
                    counter += 1
                    print(str(counter)+':', formula)
                    all_formulas.append(formula)
                    minimal_formulas.append(formula)
        elif found_bsc:
            print("Found through BSC search")
            for key, value in bsc.all_results.items():
                print(f"Size: {key}")
                counter = 0
                for formula in value:
                    counter += 1
                    print(str(counter)+':', formula)
                    all_formulas.append(formula)
                    minimal_formulas.append(formula)

    print('Max diff formula:', sep.max_diff_formula)
    print('Max diff value:', sep.max_diff)


    running_folder = '/'.join(list(positive[0].split('/'))[:-1])
    info_dict = {'folder': running_folder,
                'max_size': max_size,
                'max_depth': max_depth,
                'num_positive': len(positive),
                'num_negative': len(negative),
                'minimal_formula': ';'.join(minimal_formulas),
                'all_formulas': ';'.join(all_formulas),
                'max_diff_formula': sep.max_diff_formula,
                'total_formulas': grammar.total_formula_counter,
                'total_boolean_comb': bsc.formula_counter,
                'total_time': round(grammar.total_time+sep.separation_time+sep.PRISM_time,3),
                'grammar_times': round(grammar.total_time,3),                      
                'separation_time': round(sep.separation_time,3),
                'PRISM_time': round(sep.PRISM_time,3),
                'BSC_time': round(bsc.time,3)
                }
    heuristics_dict = {k:';'.join([str(grammar.heuristics[k]), str(grammar.heuristics_counter[k]), str(round(grammar.heuristics_times[k],3))]) for k in grammar.heuristics}
    info_dict.update(heuristics_dict)

    print(info_dict)
    with open(f'{external_folder}/{info_file}.json', 'w') as f:
        json.dump(info_dict, f)