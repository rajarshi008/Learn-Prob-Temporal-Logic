from lark import Lark, Transformer
import spot


bool_unary = ['!']
bool_binary = ['&', '|']
temporal_unary = ['X', 'F', 'G']
temporal_binary = ['U']

unary_operators = temporal_unary + bool_unary
binary_operators = temporal_binary + bool_binary

class SimpleTree:
    '''
    Class for encoding syntax Trees of formulas
    '''
    def __init__(self, label = "dummy"):	
        self.left = None
        self.right = None
        self.label = label
        self.params = None
        self.tree_size = None

    def __hash__(self):
        # return hash((self.label, self.left, self.right))
        return hash(self.label) + id(self.left) + id(self.right)
    
    def __eq__(self, other):
        if other is None:
            return False
        else:
            return self.label == other.label and self.left == other.left and self.right == other.right
    
    def __ne__(self, other):
        return not self == other
    
    def _isLeaf(self):
        return self.right is None and self.left is None
    
    def _addLeftChild(self, child):
        if child is None:
            return
        if type(child) is str:
            child = SimpleTree(child)
        self.left = child
        
    def _addRightChild(self, child):
        if type(child) is str:
            child = SimpleTree(child)
        self.right = child
    
    def addChildren(self, leftChild = None, rightChild = None): 
        self._addLeftChild(leftChild)
        self._addRightChild(rightChild)
        
        
    def addChild(self, child):
        self._addLeftChild(child)
        
    def getAllNodes(self):
        leftNodes = []
        rightNodes = []
        
        if not self.left is None:
            leftNodes = self.left.getAllNodes()
        if not self.right is None:
            rightNodes = self.right.getAllNodes()
        return [self] + leftNodes + rightNodes

    def getAllLabels(self):
        if not self.left is None:
            leftLabels = self.left.getAllLabels()
        else:
            leftLabels = []
            
        if not self.right is None:
            rightLabels = self.right.getAllLabels()
        else:
            rightLabels = []
        return [self.label] + leftLabels + rightLabels

    def __repr__(self):
        if self.left is None and self.right is None:
            return self.label
        
        # the (not enforced assumption) is that if a node has only one child, that is the left one
        elif (not self.left is None) and self.right is None:
            return self.label + '(' + self.left.__repr__() + ')'
        
        elif (not self.left is None) and (not self.right is None):
            return self.label + '(' + self.left.__repr__() + ',' + self.right.__repr__() + ')'

    def treeSize(self):
        if self.tree_size is None:
            if self.left is None and self.right is None:
                self.tree_size = 1
            else:
                leftSize=0
                rightSize=0
                if not self.left is None:
                    leftSize= self.left.treeSize()
                if not self.right is None:
                    rightSize = self.right.treeSize()
                self.tree_size = 1 + leftSize + rightSize

        return self.tree_size

class LTLFormula(SimpleTree):
    '''
    A class for encoding syntax Trees and syntax DAGs of LTL formulas
    '''
    def __init__(self, formulaArg = "dummyF"):

        self.str = None
        self.spot_formula = None
        self.tree_size = None
        if not isinstance(formulaArg, str):
            self.label = formulaArg[0]
            self.left = formulaArg[1]
            try:
                self.right = formulaArg[2]
            except:
                self.right = None
            self.str = self.prettyPrint()
            self.tree_size = self.treeSize()
            self.spot_formula = self.genSpotFormula()
        else:
            super().__init__(formulaArg)
            self.str = self.prettyPrint()
            self.tree_size = self.treeSize()
            self.spot_formula = self.genSpotFormula()
    
    def __lt__(self, other):

        if self.getDepth() < other.getDepth():
            return True
        elif self.getDepth() > other.getDepth():
            return False
        else:
            if self._isLeaf() and other._isLeaf():
                return self.label < other.label

            if self.left != other.left:
                return self.left < other.left

            if self.right is None:
                return False
            if other.right is None:
                return True
            if self.right != other.right:
                return self.right < other.right

            else:
                return self.label < other.label

    def prettyPrint(self, top=False):
        if self.str is not None:
            return self.str
        else:
            if top is True:
                lb = ""
                rb = ""
            else:
                lb = "("
                rb = ")"
            if self._isLeaf():
                return self.label
            if self.label in unary_operators:
                return self.label + lb + self.left.prettyPrint() + rb
            if self.label in binary_operators:
                return lb + self.left.prettyPrint() + rb + self.label + lb + self.right.prettyPrint() + rb

    def genSpotFormula(self):
        if self.spot_formula is None:
            if self._isLeaf():
                self.spot_formula = spot.formula(self.label)
            else:
                if self.label == 'X':
                    self.spot_formula = spot.formula.X(self.left.genSpotFormula())
                if self.label == 'F':
                    self.spot_formula = spot.formula.F(self.left.genSpotFormula())
                if self.label == 'G':
                    self.spot_formula = spot.formula.G(self.left.genSpotFormula())
                if self.label == 'U':
                    self.spot_formula = spot.formula.U(self.left.genSpotFormula(), self.right.genSpotFormula())
                if self.label == '!':
                    self.spot_formula = spot.formula.Not(self.left.genSpotFormula())
                if self.label == '&':
                    self.spot_formula = spot.formula.And([self.left.genSpotFormula(), self.right.genSpotFormula()])
                if self.label == '|':
                    self.spot_formula = spot.formula.Or([self.left.genSpotFormula(), self.right.genSpotFormula()])
                
        return self.spot_formula


    @classmethod
    def convertTextToLTLFormula(cls, formulaText):

        f = LTLFormula()
        try:
            formula_parser = Lark(r"""
                ?formula: _binary_expression
                        |_unary_expression
                        | constant
                        | variable
                !constant: "true"
                        | "false"
                _binary_expression: binary_operator "(" formula "," formula ")"
                _unary_expression: unary_operator "(" formula ")"
                variable: /x[0-9]*/
                !binary_operator: "&" | "|" | "->" | "U"
                !unary_operator: "F" | "G" | "!" | "X"

                %import common.SIGNED_NUMBER
                %import common.WS
                %ignore WS
             """, start = 'formula')


            tree = formula_parser.parse(formulaText)
            #print(tree.pretty())

        except Exception as err:
            # raise ValueError(f"can't parse formula {formulaText!r}") from err
            return cls.convertPrettyToFormula(formulaText)


        f = TreeToLTLFormula().transform(tree)
        return f

class TreeToLTLFormula(Transformer):
        def formula(self, formulaArgs):
            if not isinstance(formulaArgs[0], str): formulaArgs.insert(0, formulaArgs.pop(1))
            return LTLFormula(formulaArgs)
        def variable(self, varName):
            return LTLFormula([str(varName[0]), None, None])
        def constant(self, arg):
            return LTLFormula(str(arg[0]))
        def binary_operator(self, args):
            return str(args[0])
        def unary_operator(self, args):
            return str(args[0])



