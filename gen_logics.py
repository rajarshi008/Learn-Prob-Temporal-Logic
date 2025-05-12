from prob_logics import *
import spot
import time
import os

#STATE_OPS = ['!', '&', '|']
#PATH_OPS = ['X', 'U', 'F', 'G']

PRQUERY = "=?"

def syntax_heur(f1, f2):
    # returns true if f1 = f2 syntactically
    return syntax_equiv(f1, f2) or syntax_neg_equiv(f1, f2)

def simplify_heur(f1):
    # Basic simplication heuristics
    if f1.label == 'F':
        if f1.left.label == 'F':
            return True
    if f1.label == 'G':
        if f1.left.label == 'G':
            return True
    if f1.label == 'X':
        if f1.left.label == 'F' or f1.left.label == 'G':
            return True
    if f1.label == 'U':
        if f1.left.label == 'X' and f1.right.label == 'X':
            return True
    if f1.label == '&':
        if f1.left.label == 'G' and f1.right.label == 'G':
            return True
        if f1.left.label == 'X' and f1.right.label == 'X':
            return True
    if f1.label == '|':
        if f1.left.label == 'F' and f1.right.label == 'F':
            return True
        if f1.left.label == 'X' and f1.right.label == 'X':
            return True

def spot_syntax_heur(f1, f2):
    # returns true if f1 = f2 syntactically
    return spot_syntax_equiv(f1, f2) or spot_syntax_neg_equiv(f1, f2)

def spot_simplify_heur(f1):
    g = f1.spot_formula.simplify()
    if f1.spot_formula != g or spot.length(g) < f1.tree_size:
        #print(f1, g)
        return True
    return False
    
def spot_semantic_heur(f1, f2, c):
    #print(f1.spot_formula,f2.spot_formula, spot.are_equivalent(f1.spot_formula, f2.spot_formula))
    contain = c.contained(f1.spot_formula, f2.spot_formula) or c.contained(f2.spot_formula, f1.spot_formula)
    #equiv = c.equal(f1.spot_formula, f2.spot_formula)# contain better than equiv

    return contain

def syntax_equiv(f1, f2):
    # returns true if f1 = f2 syntactically
    if f1.tree_size != f2.tree_size:
        return False
    return f1 == f2

def syntax_neg_equiv(f1, f2):
    # only for proposition
    if f1.tree_size != 1 or f2.tree_size != 1:
        return False
    diff = abs(len(f1.label) - len(f2.label))
    if diff != 1:
        return False
    if f1.label[0] == '!' and f2.label[0] != '!':
        if f1.label[1:] != f2.label[0:]:
            return False
    if f1.label[0] != '!' and f2.label[0] == '!':
        if f1.label[0:] != f2.label[1:]:
            return False
    return True
   
def spot_syntax_equiv(f1, f2):
    return f1.spot_formula == f2.spot_formula

def spot_syntax_neg_equiv(f1, f2):
    if f1.label != '!' and f2.label != '!':
        return False
    size_diff = f1.tree_size - f2.tree_size
    if abs(size_diff) != 1:
        return False
    if size_diff == 1:
        return f1.left.spot_formula == f2.spot_formula
    return f1.spot_formula == f2.left.spot_formula


class GrammarGenPLTL:
    '''
    PLTL Grammar Generator, its enumerates LTL formulas adding a P operator
    '''
    def __init__(self, atoms, max_depth=1, max_size=3) -> None:
        self.max_depth = 1
        self.current_size = 1
        self.max_depth = max_depth
        self.max_size = max_size
        self.formula_list = {}
        self.atoms = atoms
        # Heuristics to avoid redundant formulas
        
        self.spot_containment = spot.language_containment_checker()
        self.heuristics = {'syn_eq': True, 
                            'simp_eq': True, 
                            'spot_syn_eq': True,
                            'spot_simp_eq': True,
                            'spot_sem_eq': True,
                            }
        self.heuristics_functions = {'syn_eq': syntax_heur,
                                     'simp_eq': simplify_heur,
                                        'spot_syn_eq': spot_syntax_heur,
                                        'spot_simp_eq': spot_simplify_heur,
                                        'spot_sem_eq': spot_semantic_heur,
                                        }
        
        self.heuristics_counter = {h: 0 for h in self.heuristics}
        self.heuristics_times = {h: 0 for h in self.heuristics}
        self.total_formula_counter = 0
        self.total_time = 0

    def apply_binary_heuristics(self, f1, f2):
        
        heuristic_succ = False
        if self.heuristics['syn_eq']:
            t0 = time.time()
            if self.heuristics_functions['syn_eq'](f1, f2):
                self.heuristics_counter['syn_eq'] += 1
                heuristic_succ = True
            t1 = time.time() - t0
            self.heuristics_times['syn_eq'] += t1

        if self.heuristics['spot_syn_eq']:
            t0 = time.time()
            if self.heuristics_functions['spot_syn_eq'](f1, f2):
                self.heuristics_counter['spot_syn_eq'] += 1
                heuristic_succ = True
            t1 = time.time() - t0
            self.heuristics_times['spot_syn_eq'] += t1

        if self.heuristics['spot_sem_eq']:
            t0 = time.time()
            if self.heuristics_functions['spot_sem_eq'](f1, f2, self.spot_containment):
                self.heuristics_counter['spot_sem_eq'] += 1
                heuristic_succ = True
            t1 = time.time() - t0
            self.heuristics_times['spot_sem_eq'] += t1

        return heuristic_succ

    def apply_unary_heuristics(self, f1):
        
        heuristic_succ = False
        if self.heuristics['simp_eq']:
            t0 = time.time()
            if self.heuristics_functions['simp_eq'](f1):
                self.heuristics_counter['simp_eq'] += 1
                heuristic_succ = True
            t1 = time.time() - t0
            self.heuristics_times['simp_eq'] += t1

        if self.heuristics['spot_simp_eq']:
            t0 = time.time()
            if self.heuristics_functions['spot_simp_eq'](f1):
                self.heuristics_counter['spot_simp_eq'] += 1
                heuristic_succ = True
            t1 = time.time() - t0
            self.heuristics_times['spot_simp_eq'] += t1

        return heuristic_succ
    

    def init_formulas(self):
        
        t0 = time.time()
        self.formula_list = {(d,s): set() for d in range(self.max_depth+1) for s in range(self.max_size+1)}
        self.formula_list[(0,1)] = set()
        for atom in self.atoms:
            new_formula = LTLFormula([atom, None, None])
            self.formula_list[(0,1)].add(new_formula)
            neg_formula = LTLFormula(['!'+atom, None, None])
            self.formula_list[(0,1)].add(neg_formula)
        self.current_size = 1
        t1 = time.time() - t0
        self.total_formula_counter = len(self.formula_list[(0,1)])
        self.total_time += t1

    def gen_next_size(self):
        '''
        Grammar generator now creates all possible formulas of size n+1 for all depths
        '''
        t0 = time.time()
        next_size = self.current_size + 1
        for depth in range(self.max_depth+1):
            self.formula_list[(depth,next_size)] = set()
            
            if depth != 0:
                for op in temporal_unary:
                    for left in self.formula_list[(depth-1,self.current_size)]:
                        new_formula = LTLFormula([op, left, None])
                        
                        if self.apply_unary_heuristics(new_formula):
                            continue
                        self.formula_list[(depth,next_size)].add(new_formula)

                for op in temporal_binary:
                    for size in range(1, self.current_size+1):
                        for d in range(depth):
                            for f1 in self.formula_list[(d,size)]:
                                for f2 in self.formula_list[(depth-1,self.current_size - size)]:
                                    
                                    #### Heuristics to remove redundant formulas ####
                                    if self.apply_binary_heuristics(f1, f2):
                                        continue
                                    #### End of heuristics ####

                                    new_formula1 = LTLFormula([op, f1, f2])
                                    new_formula2 = LTLFormula([op, f2, f1])
                                    
                                    #### Heuristics to remove redundant formulas ####
                                    if self.apply_unary_heuristics(new_formula1):
                                        continue
                                    if self.apply_unary_heuristics(new_formula2):
                                        continue
                                    #### End of heuristics ####
                                    self.formula_list[(depth,next_size)].add(new_formula1)
                                    self.formula_list[(depth,next_size)].add(new_formula2)

            #if depth == 0:
            for op in bool_binary:
                for size in range(1, self.current_size+1):
                    for d in range(depth+1):
                        for f1 in self.formula_list[(d,size)]:
                            for f2 in self.formula_list[(depth,self.current_size - size)]:

                                if self.apply_binary_heuristics(f1, f2):
                                    continue
                                new_formula = LTLFormula([op, f1, f2])

                                if self.apply_unary_heuristics(new_formula):
                                    continue
                                self.formula_list[(depth,next_size)].add(new_formula)
            
            self.total_formula_counter += len(self.formula_list[(depth,next_size)])
        self.current_size = next_size
        t1 = time.time() - t0
        self.total_time += t1



#### Heuristics comparison ####
# Can use these to compare the heuristics
# Conclusion: syntax equiv removes smaller number of formulas but is faster (milliseconds)
# Semantic equivalence is slower (seconds) but removes few 1000s of formulas more
'''
max_size = 6
max_depth = 3
props = ['a', 'b']

heur1 = {'syn_eq': False, 'simp_eq': False, 'spot_syn_eq': False, 'spot_simp_eq': False, 'spot_sem_eq': False}
heur2 = {'syn_eq': True, 'simp_eq': True, 'spot_syn_eq': False, 'spot_simp_eq': False, 'spot_sem_eq': False}
heur3 = {'syn_eq': False, 'simp_eq': False, 'spot_syn_eq': True, 'spot_simp_eq': False, 'spot_sem_eq': True}
heur4 = {'syn_eq': False, 'simp_eq': False, 'spot_syn_eq': True, 'spot_simp_eq': True, 'spot_sem_eq': False}
heur5 = {'syn_eq': False, 'simp_eq': False, 'spot_syn_eq': True, 'spot_simp_eq': True, 'spot_sem_eq': True}
heur6 = {'syn_eq': True, 'simp_eq': True, 'spot_syn_eq': True, 'spot_simp_eq': True, 'spot_sem_eq': True}
#heurs = [heur1, heur2, heur3, heur4, heur5]
heurs = []


# all heuristics

#print('All heuristics:')
for heur in heurs:
    print('#################################')
    t0 = time.time()
    g = GrammarGenPLTL(props, max_depth=max_depth, max_size=max_size)
    g.heuristics = heur
    g.init_formulas()
    for i in range(2, max_size+1):
        g.gen_next_size()
        len_size = 0
        for d in range(max_depth+1):
            len_size += len(g.formula_list[(d,i)])
            file_path = os.path.join('GBE-heurs', f'temp_{i}_{d}.tl')
            with open(file_path, 'w') as f:
                if g.formula_list[(d,i)]:
                    for formula in g.formula_list[(d,i)]:
                        f.write(formula.prettyPrint() + "\n")
        print('Size', i, len_size)
    t1 = time.time() - t0
    print('Time', t1)
    print(heur)
    print(g.heuristics_counter)
    print('#################################')
'''