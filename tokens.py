"""
defining tokens, ie immutable single objects that can hold value and that can represent complex state

(c) Stefan LOESCH, topaze.blue 2020. 

Licensed under the MIT license https://opensource.org/licenses/MIT
"""
__version__ = "1.2.2"
__author__ = "Stefan Loesch, topaze.blue"
__license__ = "MIT"

from collections import namedtuple, OrderedDict

class Token:
    """
    class representing "Tokens" ie single objects holding immutable state

    :strval:        the string value of the token (should be the same as the name of the object)
    :intval:        the integer value of the token (optional)
    :floatval:      the float value of the token (optional)
    :dictval:       the dict value of the token (optional)
    :listval:       the list value of the token (techically tuple; optional)
    :val:           the TokenValue object collecting all values (optional; takes precedence if present)

    NOTE

    Tokens should be thought about as constants. They are defined once, and then they exists as
    immutable singleton objects whereever they are. They are particular useful for holding state.
    For example, a queue counter variable could hold the special states EXHAUSTED and PRIMED, 
    and maybe HALTED or some other error codes. 

    As tokens are singleton objects the comparison operator to use is always `is`, not `==`.

    EXAMPLE

        class QueueState(Token):
            pass

        EMPTY       = QueueState(0, "EMPTY")
        EXHAUSTED   = QueueState(1, "EXHAUSTED")

        from .states import EMPTY, EXHAUSTED
        ...
        if queueval == EMPTY:
            queueval = prime_the_queue(...)

        while not queueval == EXHAUSTED:
            ...

    IMPORTANT

        Usually Token objects are singleton objects in the sense that they will be defined
        somewhere and imported from there, so there is one and only one of this objects present
        and a comparison with `is` is appropriate.

        There is one important exception to this however: when Tokens had been pickled and are
        restored by unpickle then the unpickled Token objects are _distinct_ from the locally
        defined ones, and therefore `is` comparisions WILL FAIL. 

        To avoid this, the objects should always be compared using `==`.

    TOKEN HIERARCHIES

    It is possible to build token hierarchies via class inheritance, like in the 
    example that follows

        class Status(Token):    pass
        class Success(Status):  pass
        class Error(Status):    pass
        
        COMPLETED           = Succes("COMPLETED")
        PAUSED              = Succes("PAUSED")
        MECHANICAL_ERROR    = Error("MECHANICAL_ERROR")
        USER_ERROR          = Error("USER_ERROR")

        isinstance(_, Status)       # True for all the above
        isinstance(_, Success)      # True for COMPLETED, PAUSED
        isinstance(_, Error)        # True for MECHANICAL_ERROR, USER_ERROR


    MAKE ROOT

    Tokens need to be globally unique in some values which does not always make sense.
    In particular when different projects are combined then it is not always feasible
    to ensure that tokens are globally unique.

    The solution to this is the makeroot() method that creates a new root hierarchy,
    or namespace so to say. Below is an example for two hierarchies that are completely
    distince.

        class LogEvent(Token): pass
        LogEvent.makeroot()
        class UserInteractionEvent(LogEvent): pass
        BOTCHAT     = UserInteractionEvent("BOTCHAT")
        CALL        = UserInteractionEvent("CALL")
        EMAIL       = UserInteractionEvent("EMAIL")
        
        class CommercialEvent(LogEvent): pass
        PURCHASE    = CommercialEvent("PURCHASE")
        ...
        

        class Comparison(Token): pass
        Comparison.makeroot()
        COMP_EQ = Comparison("EQ", listval=(operator.eq,))
        COMP_LT = Comparison("LT", listval=(operator.lt,))
        class Existence(Comparison): pass
        COMP_EX = Existence("EX")  # exists
        COMP_NX = Existence("NX")  # does not exist
    """
    __version__ = __version__

    class TokenValue:
        def __init__(s, strval=None, intval=None, floatval=None, dictval=None, listval=None):
            s.strval = strval
            s.intval = intval
            s.floatval = floatval
            s.dictval = dictval
            s.listval = listval
        
        def __repr__(s):
            return "TokenValue({}, {}, {}, {}, {})".format(s.strval, s.intval, s.floatval, s.dictval, s.listval)
            
    _register = OrderedDict()
    def __init__(s, strval=None, intval=None, floatval=None, dictval=None, listval=None, val=None):
        if val is None:
            s._val = s.TokenValue(strval, intval, floatval, dictval, listval)
        else:
            s._val = val

        if s._val.strval is None:
            raise RuntimeError("token must have a string value", s._val)

        # we now update the central token register; this register is indexed by class
        # within the class the register is organised by Token string, and this string
        # must be unique for a given class
        try:
            register = s._register[s.__class__]
        except KeyError:
            s._register[s.__class__] = OrderedDict()
            register = s._register[s.__class__]
        if s.str in register:
            raise RuntimeError("Token must be globally unique in this micro segment", s.str, s, register[s.str])
        register[s.str] = s

        # we now update the string an numerical registers, if they exist
        try:
            index = s._index
            if s.str in index:
                raise RuntimeError("Token must be globally unique in this segment", s.str, s, index[s.str])
            index[s.str] = s
        except AttributeError:
            pass

        try:
            index = s._numindex
            if s.int in index:
                raise RuntimeError("Token must be globally unique in this segment", s.int, s, index[s.int])
            index[s.int] = s
        except AttributeError:
            pass

    @classmethod
    def makeroot(cls, globalIndex=True, globalNumIndex=False):
        """
        make this class a root class (must be called BEFORE any tokens are created)

        :globalIndex:       whether all tokens in the class and its subclasses should be 
                            globally unique in STRING index and indexed (default: True)
        :globalNumIndex:    whether all tokens in the class and its subclasses should be 
                            globally unique in INT index and indexed (default: False)
        """
        cls._register = OrderedDict()
        if globalIndex:
            cls._index = OrderedDict()

        if globalNumIndex:
            cls._numindex = OrderedDict()

    @classmethod
    def byval(cls, tokenvalue, noneIfMissing=False):
        """
        retrieve a token by its (globally unique) string token value

        :tokenvalue:        the (string) value of the token
        :noneIfMissing:     if True return None upon a missing token instead of raising (default)     
        :returns:           the token instance

        this only works in token hierarchies that have been created as follows 

            class RootToken(Token): pass
            RootToken.makeroot(globalIndex=True)

        if makeroot has not been called (or called with globalIndex = False) then
        this will raise an error
        """
        index = cls._index
        try:
            token = index[tokenvalue]
        except KeyError:
            if noneIfMissing: return None
            raise KeyError("token with this string value does not exist", tokenvalue)
        return token

    @classmethod
    def bynum(cls, numvalue, noneIfMissing=False):
        """
        retrieve a token by its (globally unique) integer token value

        :numvalue:          the (int) value of the token
        :noneIfMissing:     if True return None upon a missing token instead of raising (default)     
        :returns:           the token instance

        this only works in token hierarchies that have been created as follows 

            class RootToken(Token): pass
            RootToken.makeroot(globalNumIndex=True)

        if makeroot has not been called (or called with globalNumIndex = False) then
        this will raise an error
        """
        index = cls._numindex
        try:
            token = index[numvalue]
        except KeyError:
            if noneIfMissing: return None
            raise KeyError("token with this int value does not exist", numvalue)
        return token


    @classmethod
    def includes(cls, token):
        """
        whether the token belongs to this class (or its subclasses)

        :token:     the token
        :returns:   True of the token is the the current class, False otherwise
        """
        return isinstance(token, cls)

    def isof(s, tokenclass):
        """
        whether the token belongs to this class (or its subclasses)

        :tokenclass:    the tokenclass 
        :returns:       True of this belongs to tokenclass, False otherwise
        """
        return isinstance(s, tokenclass)

    @classmethod 
    def issubtoken(cls, other):
        "whether other is a sub token class of the current class"
        return issubclass(other, cls)

    @classmethod 
    def isparenttoken(cls, other):
        "whether other is a parent token class of the current class"
        return issubclass(cls, other)

    @classmethod
    def subclasses(cls, namesOnly=True):
        """
        this token class and all its child token classes

        :namesOnly:     if True only returns the class name, otherwise the actual class
        :returns:       the class and all its subclasses THAT HAVE AT LEAST ON TOKEN 
                        INSTANTIATED; if the parent class has no instantiated tokens
                        it will not appear in the register, and therefore not on this list
        """
        result = ( c for c in cls._register if issubclass(c, cls) or c==cls)
        if namesOnly:
            result = (c.__name__ for c in result)
        return tuple(result)

    @classmethod
    def tokens(cls, strOnly=True):
        """
        all tokens in this token class and all its subclasses

        :strOnly:       if True only returns the token string, otherwise the actual instance
                        (note that names only have to be unique across a final class, so there
                        can be the same name twice)
        :returns:       a tuple of all tokens, in order of definition
        """
        result = (t  for c in cls._register if issubclass(c, cls) or c==cls 
                                                        for _,t in cls._register[c].items())
        if strOnly:
            result = (t.str for t in result)
        return tuple(result)

    @property
    def type(s):
        "the token type (equals class name)"
        return s.__class__.__name__

    @property
    def int(s):
        "int value of the token"
        return s._val.intval

    @property
    def str(s):
        "string value of the token"
        return s._val.strval

    @property
    def bytes(s):
        "bytes value of the token"
        return s._val.strval.encode()

    @property
    def float(s):
        "float value of the token"
        return s._val.floatval
        
    @property
    def dict(s):
        "dict value of the token"
        return s._val.dictval

    @property
    def list(s):
        "list value of the token"
        return s._val.listval

    @property
    def tuple(s):
        "alias for list"
        return s.list()

    @property
    def val(s):
        "the entire TokenValue object containing all values"
        return s._val

    def __str__(s):
        return s.str

    def __repr__(s):
        return "{n}(val={v})".format(n=s.__class__.__name__, v=s._val)

    def __eq__(s, other):
        return s.__class__ == other.__class__ and s.str == other.str and s.int == other.int

    def __ne__(s, other):
        return not s.__eq__(other)

    def __hash__(s):
        return hash(s._val)

