import numpy as np
import heapq as hq
import time

PRQUERY = "=?"

class Boolcomb:
    def __init__(self, max_size, max_initial_set, delta):
        self.heap = []
        self.max_initial_set = max_initial_set
        #self.max_total_set = max_total_set
        self.max_size = max_size
        self.thresholds = {}
        self.formula_vector_binary = {}
        self.size = {}
        self.all_results = {}
        self.time = 0
        self.delta = float(delta)
        self.found_size = 0
        self.formula_counter = 0

    def score(self, formula, formula_size, formula_satisfaction_vector):
        #arrange the results vector in sorted order
        
        t0 = time.time()
        positive_vector = formula_satisfaction_vector[0]
        negative_vector = formula_satisfaction_vector[1]
        combined_vector = np.sort(np.concatenate((positive_vector, negative_vector)))

        #print("Formula: ", formula, positive_vector, negative_vector)

        best_class = 0
        best_threshold = None

        # find the minimum misclassification error
        for i in range(len(combined_vector)-1):
            #if (combined_vector[i+1] - combined_vector[i]) < self.delta:
            #    continue
            threshold = (combined_vector[i] + combined_vector[i+1])/2
            curr_class = sum(positive_vector >= threshold) + sum(negative_vector < threshold)
            
            if curr_class > best_class:
                best_class = curr_class
                best_threshold = threshold

        if best_threshold is None:
            self.thresholds[formula] = 0
            return 0

        self.thresholds[formula] = best_threshold
        self.formula_vector_binary[formula] =[np.array(positive_vector >= best_threshold), np.array(negative_vector >= best_threshold)]
        # sqaure root of formula size
        formula_size_factor = np.sqrt(formula_size) + 1
        
        score = (best_class)/(formula_size_factor)
        #if formula == 'P=? [ F ("a") ]':
        #    print(formula, positive_vector, negative_vector, best_threshold)
        
        t1 = time.time()
        self.time += t1-t0
        return score


    def search(self):
        
        t0 = time.time()
        print("Heap size: ", len(self.heap))

        #print(self.heap)

        initial_list = hq.nsmallest(10, self.heap)
        found = False
        curr_max_size = self.max_size
        #print('Max size now', self.max_size)


        for elem1 in initial_list:
            curr_formula = elem1[1]
            if self.thresholds[curr_formula] < 0.5:
                continue

            for elem2 in self.heap:
                if elem1 == elem2:
                    continue
                new_formula = elem2[1]
                if self.thresholds[new_formula] < 0.5:
                    continue
                # misclass of And of two formulas
                #print("Current formula: ", curr_formula, self.formula_vector_binary[curr_formula])
                #print("New formula: ", new_formula, self.formula_vector_binary[new_formula])
                bool_comb_size = self.size[curr_formula] + self.size[new_formula] + 1
                if bool_comb_size > curr_max_size:
                    continue
                
                and_formula_satisfaction = [np.logical_and(self.formula_vector_binary[curr_formula][0], self.formula_vector_binary[new_formula][0]), np.logical_and(self.formula_vector_binary[curr_formula][1], self.formula_vector_binary[new_formula][1])]
                
                or_formula_satisfaction = [np.logical_or(self.formula_vector_binary[curr_formula][0], self.formula_vector_binary[new_formula][0]), np.logical_or(self.formula_vector_binary[curr_formula][1], self.formula_vector_binary[new_formula][1])]
                
                self.formula_counter += 2

                if and_formula_satisfaction[0].all() and not(and_formula_satisfaction[1].any()):
                    curr_formula_res = curr_formula.replace(PRQUERY, '>'+str(round(self.thresholds[curr_formula],5))) 
                    new_formula_res = new_formula.replace(PRQUERY, '>'+str(round(self.thresholds[new_formula],5)))
                    result_formula = curr_formula_res + ' & ' + new_formula_res
                    found = True
                    curr_max_size = bool_comb_size
                    self.max_size = bool_comb_size
                    try:
                        if result_formula not in self.all_results[curr_max_size]:
                            self.all_results[curr_max_size].append(result_formula)
                    except:
                        self.all_results[curr_max_size] = [result_formula]

                
                if or_formula_satisfaction[0].all() and not(or_formula_satisfaction[1].any()):
                    curr_formula_res = curr_formula.replace(PRQUERY, '>'+str(round(self.thresholds[curr_formula],5))) 
                    new_formula_res = new_formula.replace(PRQUERY, '>'+str(round(self.thresholds[new_formula],5)))
                    result_formula = curr_formula_res + ' | ' + new_formula_res
                    found = True
                    curr_max_size = bool_comb_size
                    self.max_size = bool_comb_size
                    try:
                        if result_formula not in self.all_results[curr_max_size]:
                            self.all_results[curr_max_size].append(result_formula)
                    except:
                        self.all_results[curr_max_size] = [result_formula]
                
        t1 = time.time()
        self.time += t1-t0


        if found:
            self.found_size = curr_max_size
            return True    

        return False
