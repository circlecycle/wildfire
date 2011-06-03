#global application pointer
application = False
#module level imports
import wildfire.Helpers as Helpers
import re

#global attributes
node_constraints_accumulator_ = []
node_inits_accumulator_ = []
node_uidcount_ = 0

class node:
    #attribute type lookup
    attrtypes_ = {'node_attr_defaults_': 'eval', 'node_once_constraint_regex_': 'eval', 'node_constraint_regex_': 'eval'}
    #static attributes
    node_constraint_regex_ = re.compile('^.*\$\{.*\}$')
    node_once_constraint_regex_ = re.compile('^.*\$\once{.*\}$')
    node_attr_defaults_ = {'eval':0, 'float':0.0, 'str':''}
    
    #static method: __init__
    def __init__(self, parent=None, attrs={}, topmostnode=True):
        global node_inits_accumulator_, node_attr_defaults_, application
        if topmostnode and not application:
            application = self
        self.__dict__['self'] = self
        self.__dict__['parent'] = parent
        self.__dict__['application'] = application
        self.__dict__['childNodes'] = []
        self.__dict__['constraints_'] = {}
        self.__dict__['classname'] = self.__class__.__name__
        self.__dict__['early'] = False
        self.__dict__['init'] = False
        self.__dict__['late'] = False
        self.__dict__['focus'] = False
        for key in attrs.keys():
            if self.attrtypes_.has_key(key) and type(attrs[key]) == type(""):
                typeof = self.attrtypes_[key]
                if attrs[key] == None: 
                    attrs[key] = node_attr_defaults_[typeof]
                if typeof in ['expression', 'eval']:
                    self[key] = eval(attrs[key])
                elif typeof in ['number', 'float']:
                    self[key] = float(`attrs[key]`)
                elif typeof in ['string', 'str']:
                    self[key] = str(attrs[key])
            else:
                self.__dict__[key] = attrs[key]
        self.initConstraints_()
        self.__construct__()
        self.__objectgraph__()
        node_inits_accumulator_.append(self)
        if self.classname != 'application_':
          self.touch('childNodes')
        if topmostnode:
          self.sendInits_()
    
    #static method: __construct__
    def __construct__(self, ):
        pass
    
    #static method: sendInits_
    def sendInits_(self, ):
        """I issue all early, init, constraint, late events from global accumlation buffers.
           note that i am only called at the top of any create action, not at every node init!
        """
        global node_inits_accumulator_
        toinit = node_inits_accumulator_[:]
        node_inits_accumulator_ = []
        [setattr(node, 'early', True) for node in toinit]  
        [setattr(node, 'init', True) for node in toinit]  
        self.evaluateConstraints_()
        [setattr(node, 'late', True) for node in toinit]
    
    #static method: initConstraints_
    def initConstraints_(self, ):
        """ for each string attribute on this tag, find and later process any constraints that exist """
        global node_constraints_accumulator_
        for key in self.__dict__.keys():
            if type(self[key]) is type(""):
                if self.node_constraint_regex_.search(self[key]):
                    node_constraints_accumulator_.append([self, (key, self[key][2:-1], "always")])
                elif self.node_once_constraint_regex_.search(self[key]):
                    node_constraints_accumulator_.append([self, (key, self[key][6:-1], "once")])
    
    #static method: evaluateConstraints_
    def evaluateConstraints_(self, ):
        """ when a constraint is detected it is added to singleton list without any action
            being taken. After the first stage of initialization, go back and give all those
            constraints values (now that everything exists)
        """
        global node_constraints_accumulator_
        constraints = node_constraints_accumulator_[:]
        node_constraints_accumulator_ = []
        for constraintTuple in constraints:
          node, constraint = constraintTuple
          attr, entry, ofType = constraint
          entry = entry.split('->')
          if len(entry) > 1:  watch, perform = entry
          else:               watch, perform = entry[0], entry[0]
          if ofType == "always":
            pathsToCheck = []
            constraintPaths = [x.strip() for x in watch.split(',') if x]
            for constraintPath in constraintPaths:
              fullpath = constraintPath.split('.')
              target, path = fullpath[-1], '.'.join(fullpath[:-1])
              pathsToCheck.append([path, target])
            for constraintPath in pathsToCheck:
              path, target = constraintPath
              obj = eval(path, node.__dict__)
              funcname = "_dele_%s_%s"%(path.replace('.', '_'), target)
              funcbody = "def %s(value): self.%s = %s"%(funcname, attr, perform)
              exec funcbody in node.__dict__
              obj.constrain(attr=target, func=node.__dict__[funcname], set=True)
          elif ofType == "once":
            setattr(node, attr, eval(watch, node.__dict__))
    
    #static method: constrain
    def constrain(self, attr=None, func=None, set=False):
        """ make a constraint, that is, add to constraints_ on a target node a pointer
            to a function to call when it value changes. Setting set to 
            true (the default) also sets that value on the node. This is because
            before the init is completed, there may not be value to set!
        """
        if not self.constraints_.has_key(attr):
            self.__dict__['constraints_'][attr] = []
        self.__dict__['constraints_'][attr].append(func)
        if set: func(self[attr])
    
    #static method: touch
    def touch(self, attr):
        """ set off the constraints for a given attribute without changing 
            it's value (self.x = self.x would be similar.)
        """
        if self.constraints_.has_key(attr):
          [listener(self[attr]) for listener in self.handlers_[attr]]
    
    #static method: __getitem__
    def __getitem__(self, attr):
        """make it possible to get interior nodes dictionary style"""
        return getattr(self, attr, None)
    
    #static method: __setitem__
    def __setitem__(self, attr, val):
        """make it possible to set interior nodes dictionary style"""
        setattr(self, attr, val)
    
    #static method: __setattr__
    def __setattr__(self, attr, value):
        """ and.. the very heart of delegates, events, constraints, etc! """
        self.__dict__[attr] = value
        if self.constraints_.has_key(attr):
          [listener(value) for listener in self.constraints_[attr]]
    
    #static method: animate
    def animate(self, attrname, to, dur):
        """stub that creates and returns a new Animator object for this node 
           the animator object automatically registers with the animation
           event loop. 
        """
        return Animation.Animator(self, attrname, self[attrname], to, dur)

    #builtin method: __objectgraph__
    def __objectgraph__(self, ):
        pass


#module level imports
class attribute(node):
    #attribute type lookup
    attrtypes_ = {'type': 'str', 'name': 'str', 'value': 'str'}
    #static attributes
    type = 'expression'
    
    #static method: __construct__
    def __construct__(self, ):
        types = {'expression':None, 'number':float, 'string':str}
        if not self['value']: 
            self['value'] = "None"
        if type(self.value) == type(""):
            typeof = types[self.type]
        if self.parent[self.name]:
            self.value = self.parent[self.name]
        if self.type == 'expression':
            value = self.value
            if type(self.value) == type(""):
                value = eval(str(self.value))
        else:
            value = typeof(self.value)
        self.parent[self.name] = value

    #builtin method: __objectgraph__
    def __objectgraph__(self, ):
        pass


#module level imports
class method(node):
    #attribute type lookup
    attrtypes_ = {'args': 'str', 'name': 'str'}
    #static attributes
    args = 'val=False'
    
    #static method: __construct__
    def __construct__(self, ):
        if self.args is None: self.args = ''
        script = ["def %s(%s):"%(self.name, self.args)]
        script.extend( ["    %s"%(x) for x in Helpers.normalizeScript(self.text).split('\n')] )
        script = "\n".join(script)
        try:  exec script in self.parent.__dict__
        except Exception, msg: raise Exception("bad syntax in python block:\n %s" % msg)

    #builtin method: __objectgraph__
    def __objectgraph__(self, ):
        pass


#module level imports
class handler(node):
    #attribute type lookup
    attrtypes_ = {'on': 'str', 'set': 'eval', 'delegate': 'eval', 'reference': 'eval'}
    #static attributes
    delegate = False
    set = False
    
    #static method: __construct__
    def __construct__(self, ):
        """make a reference method that we can use to evaluate referenced nodes
        """
        global node_uidcount_
        if not self.delegate:
            self.funcname = self['name'] or "_%s_%s"%(self.on, node_uidcount_)
            node_uidcount_ += 1
            args = self['args'] or "value"
            script = ["def %s(%s):"%(self.funcname, args)]
            script.extend( ["    %s"%(x) for x in Helpers.normalizeScript(self.text).split('\n')] )
            script = '\n'.join(script)
            try:  exec script in self.parent.__dict__
            except Exception, msg: raise "bad syntax in python block\n\n"+`msg`
        if self['reference']:
            self.parent.constrain(attr='early', func=self._reference)
        else:
            self.parent.constrain(attr=self.on, func=(self.delegate or self.parent.__dict__[self.funcname]), set=self.set )
    
    #static method: _reference
    def _reference(self, val=False):
        target = eval(self.reference, self.parent.__dict__)
        target.constrain(attr=self.on, func=(self.delegate or self.parent.__dict__[self.funcname]))

    #builtin method: __objectgraph__
    def __objectgraph__(self, ):
        pass


#module level imports
class view(node):
    #attribute type lookup
    attrtypes_ = {'opacity': 'float', 'sizing': 'str', 'bgcolor': 'str', 'focusable': 'eval', 'image': 'eval', 'height': 'float', 'visible': 'eval', 'width': 'float', 'y': 'float', 'x': 'float', 'aligned': 'str', 'transparent': 'eval'}
    #static attributes
    visible = True
    transparent = True
    opacity = float('0')
    bgcolor = 'white'
    x = float('0')
    y = float('0')
    width = float('0')
    height = float('0')
    focusable = True
    aligned = 'right'
    sizing = 'auto'
    
    #static method: __init__
    def __init__(self, ):
        self.compute_transparency_()
    
    #static method: getLayer
    def getLayer(self, ):
        return self.parent.childViews.index(self)
    
    #static method: setLayer
    def setLayer(self, ):
        del self.parent.childViews[self.parent.childViews.index(self)]
        self.parent.childViews.insert(position, self)
        self.parent.touch('childViews')
    
    #static method: bringToFront
    def bringToFront(self, ):
        if self.parent.childViews.index(self) < len(self.parent.childViews) - 1:
          del self.parent.childViews[self.parent.childViews.index(self)]
          self.parent.childViews.append(self)
          self.parent.touch('childViews')
    
    #static method: sendToBack
    def sendToBack(self, ):
        if self.parent.childViews.index(self) > 0:
          del self.parent.childViews[self.parent.childViews.index(self)]
        self.parent.childViews.insert(0, self)
        self.parent.touch('childViews')
    
    #static method: computeSize_
    def computeSize_(self, val=False):
        w = self.getWidth()
        if self.width != w: self.width = w
        h = self.getHeight()
        if self.height != h: self.height = h
    
    #static method: getWidth
    def getWidth(self, ):
        return [v.x+v.width for v in self.childViews if v.sizing != 'skip']
    
    #static method: getHeight
    def getHeight(self, ):
        views = [v.y+v.height for v in self.childViews if v.sizing != 'skip']
        if views: return max(views)
        else:     return self.height
    
    #static method: compute_transparency_
    def compute_transparency_(self, val=False):
        if self['bgcolor'] or self['image']: 
          self.transparent = False
        else:
          self.transparent = True
    
    #static method: center_
    def center_(self, ):
        self.x = (self.parent.width/2)-(self.width/2)
    
    #static method: middle_
    def middle_(self, ):
        self.y = (self.parent.height/2)-(self.height/2)
    
    #static method: absx
    def absx(self, x):
        return x - self.parent.absX_
    
    #static method: absy
    def absy(self, y):
        return y - self.parent.absY_

    #builtin method: __objectgraph__
    def __objectgraph__(self, ):
        self.anon_0_ = handler(self, {'on': 'init', 'text': "\n            if 'once' in self.sizing or 'skip' in self.sizing:\n              self.computeSize_()\n        "}, topmostnode=False)
        self.anon_1_ = handler(self, {'on': 'late', 'text': '\n            #use the aligned attribute to set up constraints that vertically or horizontally center the view\n            if self.aligned:\n              #if the view is aligned horizontally "center"\n              if \'center\' in self.aligned:\n                self.parent.constrain(attr="width", func=self.center_, set=True)\n\n              #if the view is aligned vertically "middle"\n              if \'middle\' in self.aligned:\n                self.parent.constrain(attr="height", func=self.middle_, set=True)\n        '}, topmostnode=False)


#module level imports
class printhi(node):
    #attribute type lookup
    attrtypes_ = {}
    
    #static method: something
    def something(self, ):
        return "something()"

    #builtin method: __objectgraph__
    def __objectgraph__(self, ):
        self.anon_2_ = handler(self, {'on': 'init', 'text': '\n            print "hi"\n        '}, topmostnode=False)


#module level imports
class application_(node):
    #attribute type lookup
    attrtypes_ = {}

    #builtin method: __objectgraph__
    def __objectgraph__(self, ):
        self.anon_3_ = handler(self, {'on': 'init', 'text': '\n        #self.somenumber = 444\n        print "outer inits fired"\n    '}, topmostnode=False)
        self.anon_4_ = node(self, {'test': '${application.testvalue}', 'text': '', 'nexttest': '${application.test.somevalue}'}, topmostnode=False)
        self.anon_4_.anon_5_ = handler(self.anon_4_, {'on': 'init', 'text': '\n            print "inner inits fired"\n        '}, topmostnode=False)
        self.anon_4_.anon_6_ = handler(self.anon_4_, {'on': 'late', 'text': '\n            print "inner late fired"\n            self.foo()\n            print "test constraint:", self.test\n            print "next constraint:", self.nexttest\n        '}, topmostnode=False)
        self.anon_4_.anon_7_ = method(self.anon_4_, {'text': '\n            print "foo fired"\n            print application.test.something()\n        ', 'name': 'foo'}, topmostnode=False)
        self.test = printhi(self, {'text': '', 'somevalue': '${application.somenumber}', 'name': 'test'}, topmostnode=False)

#Kick off the application
if __name__ == '__main__':
    application = application_(None, attrs={'somenumber': '667', 'name': 'application_', 'testvalue': 'testvalue received'})