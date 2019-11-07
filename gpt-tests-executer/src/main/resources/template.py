"""
Simple yet versatile template library in python.
You can find an example at the end of this file.
"""
import re
from enum import Enum


class Token(Enum):
    """Template token types"""
    ID = 0
    INDEX = 2
    IF = 3
    ELSE = 4
    END = 6
    COLOMN = 7
    TEXT = 8
    FOREACH = 9
    SPACE = 10

def __clean_txt__(text):
    res = ''
    flag = False
    for char in text:
        if flag:
            res += char
            flag = False
        elif char == '\\':
            flag = True
        else:
            res += char
    return res


def __token__(text):
    if text.startswith('$'):
        if text[1:].isdigit():
            return (int(text[1:]), Token.INDEX)
        return (text[1:].split('.')[:], Token.ID)
    token = Token.TEXT
    if text == "foreach":
        token = Token.FOREACH
    elif text == "if":
        token = Token.IF
    elif text == "else":
        token = Token.ELSE
    elif text == "end":
        token = Token.END
    return (__clean_txt__(text), token)


def __get_next__(tokens, token):
    for tkn in tokens:
        if tkn[1] == token:
            return tkn
    return None


def __get_next_it__(tokens, token):
    for i, tkn in enumerate(tokens):
        if tkn[1] == token:
            return tkn, i
    return None, -1


def __tokenize__(text):
    res = []
    string = ""
    skip_flag = False
    for char in text:
        if skip_flag:
            string += char
            skip_flag = False
        elif char == '\\':
            res.append(__token__(string))
            string = char
            skip_flag = True
            continue
        else:
            if char == ':':
                if string != '':
                    res.append(__token__(string))
                res.append((':', Token.COLOMN))
                string = ''
            elif char == ' ':
                if string:
                    res.append(__token__(string))
                    res.append((" ", Token.SPACE))
                string = ''
            elif char == '$':
                if string:
                    res.append(__token__(string))
                string = '$'
            elif len(string) > 1 and string[0] == '$' and string[1:].isdigit() and not char.isdigit():
                res.append(__token__(string))
                string = char
            elif string and string[0] == '$' and not (char.isalnum() or char == '_'):
                res.append(__token__(string))
                string = char
            else:
                string += char
    if string:
        res.append(__token__(string))
    return res


def __make_block__(text, end_block='end'):
    count = 1
    op_list = list(re.finditer(r"\$\{([^}]+)\}", text, re.MULTILINE))
    for oper in op_list:
        if oper.group(1).startswith('if'):
            count += 1
        elif oper.group(1).startswith(end_block):
            count -= 1
            if count == 0:
                return text[:oper.start()], text[:oper.end()]
    return text, text


class Evaluator:
    """Evaluator for template operators"""
    def __init__(self, **kwargs):
        self.kwargs = kwargs

    def get_value(self, kw_k):
        """Get a nested value from the argument list"""
        exp = self.kwargs.get(kw_k[0], "==None==")
        kw_k = kw_k[1:]
        while kw_k and isinstance(exp, dict):
            exp = exp[kw_k[0]]
            kw_k = kw_k[1:]
        return exp

    def __eval_foreach__(self, tokens):
        kid = __get_next__(tokens, Token.ID)
        klist = self.get_value(kid[0])
        _, skip = __get_next_it__(tokens, Token.COLOMN)
        tmpl = tokens[skip+1:]
        if not isinstance(klist, list):
            return "==ERR=="
        res = ""
        for ele in klist:
            for t_ele in tmpl:
                if t_ele[1] == Token.INDEX and isinstance(ele, list):
                    res += str(ele[t_ele[0]])
                elif t_ele[1] == Token.ID:
                    if not t_ele[0][0]:
                        res += str(ele)
                    else:
                        if isinstance(ele, dict) and t_ele[0][0] in ele:
                            res += str(ele[t_ele[0][0]])
                        else:
                            res += str(self.get_value(t_ele[0]))
                else:
                    res += str(t_ele[0])
            res += "\n"
        return res[:-1]

    def __eval_if__(self, __condition, __inner):
        if_block = __make_block__(__inner, "else")
        else_block = __inner[len(if_block[1]):]
        if_block = if_block[0]
        if isinstance(__condition, bool) and __condition:
            return self.evals(if_block)
        return self.evals(else_block)

    def evals(self, block):
        """Evaluate block of the template"""
        res = block
        op_list = list(re.finditer(r"\$\{([^}]+)\}", res, re.MULTILINE))
        while op_list:
            oper = op_list[0]
            inside = oper.group(1)
            tokens = __tokenize__(inside)
            if tokens:
                token = tokens[0][1]
                if token == Token.IF:
                    block = __make_block__(res[oper.end():])
                    kid = __get_next__(tokens, Token.ID)
                    if_res = self.__eval_if__(self.get_value(kid[0]), block[0])
                    text = oper.group(0)+block[1]
                    res = res.replace(text, if_res)
                elif token == Token.FOREACH:
                    res = res.replace(oper.group(0), self.__eval_foreach__(tokens))
                else:
                    res = res.replace(oper.group(0), "", 1)
            else:
                res = res.replace(oper.group(0), "", 1)
            op_list = list(re.finditer(r"\$\{([^}]+)\}", res, re.MULTILINE))
        return res


class Template:
    """
    HTML Document template

    Parameters:
    -----------
     - template: text source of the html template
    """
    def __init__(self, template):
        self.__template__ = template
        self.__tags__ = re.finditer(r"\$\(([^)]+)\)", template, re.MULTILINE)
        self.__operator__ = re.finditer(r"\$\{([^}]+)\}", template, re.MULTILINE)

    def generate(self, **kwargs):
        """
        Generates html page from template.

        Parameters:
        -----------
         - kwargs: optional parameter for the template
        """
        evals = Evaluator(**kwargs)
        res = self.__template__[:]
        for match in self.__tags__:
            key = match.group(1)
            kw_k = key.split('.')
            value = evals.get_value(kw_k)
            res = res.replace(match.group(0), value, 1)
        res = evals.evals(res)

        return res


if __name__ == '__main__':
    TEMPLATE_SOURCE = """
    <h1>$(title)</h1>
    This is an example of a teplate named: $(name)<br>

    A part of simple text sostitution the template support
    some basic operations:<br>
    ${foreach $listofint: - $</br>} 

    `foreach` will itereate a list and use the template row (after the colomn) to display its values.
    You can use `$` for getting the i^th element of the  list but if the element is a list you can use
    `$j` to take the j^th element of the i^th element of the list. Or even more if the element is a dict you
    can use `$key` to use the value of the coressponding key.<br>

    ${foreach $listoflist: <b>$0</b>: $1<br>}
    ${foreach $listofdict: <b>$label</b>: $value</br>}

    If the key is not inside the row element ti will try to use a global key:<br>

    ${foreach $listofdict: <b>$label</b>($title): $value.</br>}

    Another functionality is the `if` `else` `end`:<br>
    ${if $some_boolean_value}
    Your block<br>
    ${else}
    Optional else block code <br>
    ${end}
    The else is totally optional and of course all of this can be nested.<br>

    """
    TEMPLATE = Template(TEMPLATE_SOURCE)
    LIST = list(range(10))
    LISTOFLIST = [['Abc', 10], ['Def', 11], ['Ghi', 12]]
    LISTOFDICT = [
        {
            'label': 'Jlm',
            'value': 13
        },
        {
            'label': 'Nop',
            'value': 14
        }
    ]

    print(TEMPLATE.generate(title='Example Title',
                            name='Example Name',
                            listofint=LIST,
                            listoflist=LISTOFLIST,
                            listofdict=LISTOFDICT,
                            some_boolean_value=False))
