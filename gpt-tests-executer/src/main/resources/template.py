"""
Simple yet versatile template library in python.
You can find an example at the end of this file.
"""
import re
from enum import Enum
from collections.abc import Iterable


__LT__ = '{{' # default left tag
__RT__ = '}}' # default right tag
__MAX_STR_LEN__ = 60 # maximum string length for the pretty print


class _TokenType(Enum):
    """Template token types"""
    TEXT = -2
    VARIABLE = 0
    FOREACH = 1
    IF = 2
    ELSE = 3
    END = 4
    ERROR = -1


def __parse_args__(text):
    args = text.split(' ')
    res = []
    for arg in args:
        if arg and arg[0] == '.':
            res.append(_Variable(arg))
    return res


def __get_var__(args):
    for arg in args:
        if isinstance(arg, _Variable):
            return arg
    return _Error("no variable found")


def __clean_text__(text):
    text = re.sub(r'[ |\t]+', ' ', text)
    text = re.sub(r'[ |\t]+\n', '\n', text)
    text = re.sub(r'\n+', '\n', text)
    return text


class _Token:
    def __init__(self, text, ttype, arguments=None):
        self.__text__ = text
        self.__ttype__ = ttype
        self.__arguments__ = arguments

    def eval(self, context):
        """Evaluate token"""

    def text(self):
        """get token raw text"""
        return self.__text__

    def type(self):
        """get token type"""
        return self.__ttype__

    def __repr__(self):
        printable = self.__text__.replace("\n", " ")
        printable = re.sub(r'\s+', ' ', printable)
        if not printable:
            return ''
        if printable[0] == ' ':
            printable = printable[1:]
        if len(printable) > __MAX_STR_LEN__:
            printable = printable[:__MAX_STR_LEN__-3]+'...'
        ttype = str(self.type())[11:]
        return f"{ttype}: {printable}"

    def pprint(self, starts=""):
        """pretty print"""
        print(starts+self.__repr__())


class _Text(_Token):
    def __init__(self, text):
        _Token.__init__(self, text, _TokenType.TEXT)

    def eval(self, context):
        return self.text()


class _Variable(_Token):
    def __init__(self, text):
        _Token.__init__(self, text, _TokenType.VARIABLE, text.split('.'))

    def eval(self, context):
        var = context.var(self.__arguments__)
        if var is not None:
            return var
        return f"Error: variable {self.__text__} not found\n"

    def name(self):
        """variable name"""
        return self.__arguments__


class _Error(_Token):
    def __init__(self, text):
        _Token.__init__(self, text, _TokenType.ERROR)

    def eval(self, context):
        return f"Error: {self.__text__}"


class _If(_Token):
    @staticmethod
    def __parse__(text):
        return __parse_args__(text[2:])[0]

    def __init__(self, text, body):
        _Token.__init__(self, text, _TokenType.IF, arguments=_If.__parse__(text))
        if isinstance(body, list):
            if_body = body
            else_body = None
        elif isinstance(body, tuple):
            if_body = body[0]
            else_body = body[1]
        self.__body__ = if_body
        self.__else__ = else_body

    def eval(self, context):
        cond = self.__arguments__.eval(context)
        if isinstance(cond, bool) and cond:
            return context.eval(self.__body__)
        if self.__else__:
            return context.eval(self.__else__)
        return ""

    def pprint(self, starts=""):
        _Token.pprint(self, starts)
        for ele in self.__body__:
            ele.pprint(' '+starts)
        if self.__else__:
            print(f' {starts}ELSE:')
            for ele in self.__else__:
                ele.pprint('  '+starts)


class _Foreach(_Token):
    @staticmethod
    def __parse__(text):
        inner = text[7:]
        if " in " in inner:
            inner = inner.split(' in ')
            new_var = __get_var__(__parse_args__(inner[0]))
            list_var = __get_var__(__parse_args__(inner[1]))
            return (new_var, list_var)
        return _Error(f"`{text}` foreach expression is malformed")

    def __init__(self, text, body):
        _Token.__init__(self, text, _TokenType.FOREACH, arguments=_Foreach.__parse__(text))
        self.__body__ = body

    def eval(self, context):
        if isinstance(self.__arguments__, _Error):
            return self.__arguments__.eval(context)
        res = ""
        listvar = self.__arguments__[1].eval(context)
        elevar = self.__arguments__[0]
        if not isinstance(listvar, str) and isinstance(listvar, Iterable):
            for listel in listvar:
                cnt = context.new([(elevar, listel)])
                res += cnt.eval(self.__body__)
        else:
            res = "ERROR: foreach variable is not iterable"
        return res

    def pprint(self, starts=""):
        _Token.pprint(self, starts)
        for ele in self.__body__:
            ele.pprint(' '+starts)


def __token_type__(text, lt_n, rt_n, flag=False):
    if not flag:
        return text, _TokenType.TEXT
    if text[0] == '\\':
        return text[1:], _TokenType.TEXT
    inner = text[lt_n:-rt_n]
    ttype = _TokenType.ERROR
    if inner[0] == '.':
        ttype = _TokenType.VARIABLE
    elif inner == 'end':
        ttype = _TokenType.END
    elif inner == 'else':
        ttype = _TokenType.ELSE
    elif inner.startswith(r'foreach '):
        ttype = _TokenType.FOREACH
    elif inner.startswith(r'if '):
        ttype = _TokenType.IF
    return inner, ttype


def __tokenizer__(text, left_t=__LT__, right_t=__RT__):
    tokens = []
    token = ''
    status = 0
    i = 0
    lt_n = len(left_t)
    rt_n = len(right_t)
    while i < len(text):
        char = text[i]
        token += char
        if status == 0 and len(token) >= lt_n and token[-lt_n:] == left_t:
            split = lt_n
            split += 1 if (len(token) > lt_n and token[-lt_n - 1] == '\\') else 0
            tokens.append(__token_type__(token[:-split], lt_n, rt_n))
            token = token[-split:]
            status = 1
        elif status == 1 and len(token) >= rt_n and token[-rt_n:] == right_t:
            tokens.append(__token_type__(token, lt_n, rt_n, True))
            status = 0
            token = ''
        i += 1
    if token:
        tokens.append(__token_type__(token, lt_n, rt_n))
    return tokens


def __token__(token, body=None):
    text, ttype = token
    if ttype == _TokenType.TEXT:
        return _Text(text)
    if ttype == _TokenType.VARIABLE:
        return _Variable(text)
    if ttype == _TokenType.IF:
        return _If(text, body)
    if ttype == _TokenType.FOREACH:
        return _Foreach(text, body)
    return _Error(text)


def __parse__(tokens):
    block = []
    i = 0
    while i < len(tokens):
        token = tokens[i]
        if token[1] == _TokenType.END:
            return block, i
        if token[1] in set([_TokenType.IF, _TokenType.FOREACH]):
            sblock, counter = __parse__(tokens[i+1:])
            i += counter + 1
            block.append(__token__(token, sblock))
        elif token[1] == _TokenType.ELSE:
            sblock, counter = __parse__(tokens[i+1:])
            block = (block, sblock)
            return block, i + counter + 1
        else:
            block.append(__token__(token))
        i += 1
    return block, i


class _Context:
    def __init__(self, variables, parent=None):
        self.__vars__ = variables
        self.__parent__ = parent

    def __get_var__(self, var):
        if (len(var) == 1 and var[0] == '') or var[1] == '':
            return self.__vars__
        if var[0] and not var[0] in self.__vars__:
            return None
        value = self.__vars__[var[0]] if var[0] else self.__vars__
        var = var[1:]
        while var:
            key = var[0]
            if key.isdigit():
                key = int(key)
                value = value[key]
            elif key in value:
                value = value[key]
            else:
                return None
            var = var[1:]
        return value

    def var(self, var):
        """
        get value of a variable inside the current context
        """
        if not var:
            return None
        value = self.__get_var__(var)
        if value is not None:
            return value
        if self.__parent__:
            return self.__parent__.var(var)
        return None

    def eval(self, body):
        """evaluate body"""
        res = ""
        for node in body:
            res += str(node.eval(self))
        return res

    def new(self, variables=None):
        """create a new child context"""
        names = {}
        if variables:
            for var, value in variables:
                name = var.name()
                if not name[1]:
                    names = value
                else:
                    names[name[1]] = value
        cnt = _Context(names, parent=self)
        return cnt

    def parent(self):
        """
        Get parent context
        """
        return self.__parent__


def __print_ast__(ast, space=""):
    for node in ast:
        if isinstance(node, list):
            __print_ast__(node, space=space+" ")
        else:
            node.pprint(space)


class Template:
    """
    HTML Document template

    Parameters:
    -----------
     - template: text source of the html template
    """
    def __init__(self, template):
        self.__template__ = template
        self.__tokens__ = __tokenizer__(template)
        self.__ast__, _ = __parse__(self.__tokens__)

    def print_ast(self):
        """print template ast"""
        for node in self.__ast__:
            if isinstance(node, list):
                __print_ast__(node, space=" ")
            else:
                node.pprint()

    def generate(self, **kwargs):
        """
        Generates html page from template.

        Parameters:
        -----------
         - kwargs: optional parameter for the template
        """
        context = _Context(dict(kwargs))
        return __clean_text__(context.eval(self.__ast__))


if __name__ == '__main__':
    TEMPLATE_SOURCE = """
    <h1>{{.title}}</h1>
    This is an example of a teplate named: {{.name}}<br>

    All template functionality are inside \{{...}} blocks.<br>
    A part of simple text sostitution the template support
    some basic operations:<br>
    {{foreach . in .list}}  
        - {{.}}<br/>
    {{end}} 

    `foreach` will itereate a list and use the template row (after the colomn) to display its values.
    You can use `.` for getting the i^th element of the  list but if the element is a list you can use
    `.j` to take the j^th element of the i^th element of the list. Or even more if the element is a dict you
    can use `.key` to use the value of the coressponding key.<br>

    {{foreach . in .listoflist}}
        <b>{{.0}}</b>: {{.1}}<br>
    {{end}}

    If the key is not inside the row element ti will try to use a global key:<br>

    {{foreach . in .listofdict}}
        <b>{{.label}}</b>({{.title}}): {{.value}}</br>
    {{end}}

    Another functionality is the `if` `else` `end`:<br>
    {{if .some_boolean_value}}
        Your block<br>
    {{else}}
        Optional else block code <br>
    {{end}}
    The else is totally optional and of course all of this can be nested.<br>
    {{if .condition}}
    The condition is true<br>
    {{end}}
    """
    TEMPLATE = Template(TEMPLATE_SOURCE)
    print(TEMPLATE.generate(title='TEST',
                            name='Name',
                            list=list(range(10)),
                            listoflist=[[0, 1], [1, 1], [2, 3]],
                            listofdict=[{'label': 'id', 'value': 0},
                                        {'label': 'name', 'value': 'martino'}],
                            condition=True
                            ))