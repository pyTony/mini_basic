""" pretty module version 2011 alpha 0.3
    module for printing sequences nicely

    pretty.string: make pretty string with given indent_level, step between indents, end character, f (typically str/repr), 
    character between items and brackets

    pretty.printer:  printing of the pretty string

    TODO:   ONLY list, tuple, set and frozenset prettying implemented! Other types are printed with function f.
            Must add three parts logic to add dict printing!
"""
def string(data, indent_level = 0, step = 2, end = '\n', f = repr, between = ',', brackets = None) :
    """ data = what to print, indent_level = starting indentation, step = step size for indention, end = what to put in end of lines
        brackets changes the top level brackets only, same with between"""
    startend = {list : '[]', tuple : '()',  set: '{}', frozenset: ('frozenset([','])')}
    if type(data) in startend :
        s, e = brackets or startend[type(data)]
        pr = (string(item, indent_level + step, step, end, f) for item in data)
        return end + ' ' * indent_level+step*' ' + s + (('%s ' % between) if between else '').join(pr) + e
    return f(data) if not brackets else (f(data).join('  ').join(brackets))

def printer(*args,**kwargs):
    """ passes arguments to string and prints result"""
    print(string(*args, **kwargs))

if __name__ == '__main__':
    from pprint import pprint
    t = list(map(chr, range(32,60)))
    t[10] = [range(5) for _ in range(5)]
    print('Regular')
    print(t)
    pprint('Standard pprint')
    pprint(t)
    pprint('\n')
    printer('Last but not least pretty version!', brackets = ['*'*40]*2, f=str.upper)
    printer(t, step = 1)
    printer(t, step = 4, indent_level = 20)
    printer('\n')
    printer(tuple('abcd')+([1,2,3,4],), between=' &', f=str, brackets = '<>', step = 10)
    stuff = ['spam', 'eggs', 'lumberjack', 'knights', 'ni']
    tup = ('spam', ('eggs', ('lumberjack', ('knights', ('ni', ('dead', ('parrot', ('fresh fruit',))))))))
    printer(tup, brackets=('Items(',')'), step=1)
    printer(frozenset(stuff))
