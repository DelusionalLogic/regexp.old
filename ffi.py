#!/bin/python3

from enum import Enum

from cffi import FFI

ffi = FFI()

lib = ffi.dlopen('./libregexp.so')
print('Loaded lib {0}'.format(lib))

# Describe the data type and function prototype to cffi.
ffi.cdef('''
    /* definition	number	opnd?	meaning */
    #define	END	0	/* no	End of program. */
    #define	BOL	1	/* no	Match beginning of line. */
    #define	EOL	2	/* no	Match end of line. */
    #define	ANY	3	/* no	Match any character. */
    #define	ANYOF	4	/* str	Match any of these. */
    #define	ANYBUT	5	/* str	Match any but one of these. */
    #define	BRANCH	6	/* node	Match this, or the next..\&. */
    #define	BACK	7	/* no	"next" ptr points backward. */
    #define	EXACTLY	8	/* str	Match this string. */
    #define	NOTHING	9	/* no	Match empty string. */
    #define	STAR	10	/* node	Match this 0 or more times. */
    #define	PLUS	11	/* node	Match this 1 or more times. */
    #define	OPEN	20	/* no	Sub-RE starts here. */
                                /*	OPEN+1 is number 1, etc. */
    #define	CLOSE	30	/* no	Analogous to OPEN. */

    #define NSUBEXP  10
    typedef struct regexp {
        char *startp[NSUBEXP];
        char *endp[NSUBEXP];
        char regstart;              /* Internal use only. */
        char reganch;               /* Internal use only. */
        char *regmust;              /* Internal use only. */
        int regmlen;                /* Internal use only. */
        char program[];     /* Unwarranted chumminess with compiler. */
    } regexp;

    typedef struct {
        uint16_t location;
        uint8_t op;
        uint16_t offset;

        uint16_t cmd;
        char* str;
    } regpart;

    extern regexp *regcomp(const char *re);
    extern int regexec(regexp *rp, const char *s);
    extern void regsub(const regexp *rp, const char *src, char *dst);
    extern void regerror(char *message);
    extern char * regnext(register char *p);
    extern char* regchk(char* prog);
    void regdump(regexp *r);

    size_t regsplit(char* prog, regpart* part, size_t index);
    size_t regsplit_start(char* prog, regpart* part);
''')


class Opcode(Enum):
    END = 0
    BOL = 1
    EOL = 2
    ANY = 3
    ANYOF = 4
    BRANCH = 6
    BACK = 7
    EXACTLY = 8
    NOTHING = 9
    START = 10
    PLUS = 11
    OPEN = 20
    OPEN1 = 21
    OPEN2 = 22
    OPEN3 = 23
    OPEN4 = 24
    OPEN5 = 25
    OPEN6 = 26
    OPEN7 = 27
    OPEN8 = 28
    OPEN9 = 29
    CLOSE = 30
    CLOSE1 = 31
    CLOSE2 = 32
    CLOSE3 = 33
    CLOSE4 = 34
    CLOSE5 = 35
    CLOSE6 = 36
    CLOSE7 = 37
    CLOSE8 = 38
    CLOSE9 = 39


class Node(object):
    def __init__(self, pos, nxt):
        self.pos = pos
        self.nxt = nxt

    def __str__(self):
        return f"<Node {type(self)} {self.pos} -> {self.nxt}>"


class EndNode(Node):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class BolNode(Node):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.next = None


class EolNode(Node):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.next = None


class AnyNode(Node):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.next = None


class AnyOfNode(Node):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.next = None


class BranchNode(Node):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.next = None
        self.alt = None

    def __str__(self):
        return f"<Node {type(self)} {self.pos} -> \n{self.next} | \n{self.alt}>"


class BackNode(Node):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.next = None


class ExactlyNode(Node):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.next = None


class NothingNode(Node):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.next = None


class StarNode(Node):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.next = None
        self.alt = None


class PlusNode(Node):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.next = None
        self.alt = None


class OpenNode(Node):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.next = None


class CloseNode(Node):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.next = None


def parse(part):
    op = part.op
    common = {
        "pos": part.location,
        "nxt": part.offset,
    }

    if op == lib.END:
        node = EndNode(
            **common
        )
        yield node
    else:
        if op == lib.BOL:
            node = BolNode(
                **common
            )
        elif op == lib.EOL:
            node = EolNode(
                **common
            )
        elif op == lib.ANY:
            node = AnyNode(
                **common
            )
        elif op == lib.ANYOF:
            node = AnyOfNode(
                **common
            )
        elif op == lib.BRANCH:
            arg = part.cmd
            node = BranchNode(
                **common
            )
        elif op == lib.BACK:
            node = BackNode(
                **common
            )
        elif op == lib.EXACTLY:
            node = ExactlyNode(
                **common
            )
        elif op == lib.NOTHING:
            node = NothingNode(
                **common
            )
        elif op == lib.STAR:
            node = StarNode(
                **common
            )
        elif op == lib.PLUS:
            node = PlusNode(
                **common
            )
        elif op >= lib.OPEN and op <= lib.OPEN + 9:
            node = OpenNode(
                **common
            )
        elif op >= lib.CLOSE and op <= lib.CLOSE + 9:
            node = CloseNode(
                **common
            )
        yield node

        node.next = yield common["nxt"]

        if op == lib.BRANCH:
            node.alt = yield arg
        elif op == lib.STAR:
            node.alt = yield arg
        elif op == lib.PLUS:
            node.alt = yield arg

    return node


def parseProg(prog):
    waiting_on = {}
    completed = {}
    active = set()

    part = ffi.new("regpart*")
    index = lib.regsplit_start(prog, part)

    from pprint import pprint
    while part.op != lib.END:
        index = lib.regsplit(prog, part, index)

        continuation = parse(part)

        completed[part.location] = continuation.send(None)

        active.add((continuation, None))

        while active:
            (continuation, value) = active.pop()
            try:
                dependant = continuation.send(value)

                print(f"something is waiting on {dependant}")

                # We are yielding
                if dependant in completed:
                    active.add((continuation, completed[dependant]))
                    continue
                if dependant not in waiting_on:
                    waiting_on[dependant] = []
                waiting_on[dependant].append(continuation)
            except StopIteration as stop:
                value = stop.value
                print(f"Finished {value}")

                # We are done with the parse
                completed[value.pos] = value
                pprint(waiting_on)
                if value.pos in waiting_on:
                    print(f"Marking those waiting for {value.pos}<{type(value)}> as active")
                    for continuation in waiting_on[value.pos]:
                        active.add((continuation, value))
                    del waiting_on[value.pos]
    pprint(waiting_on)
    pprint(active)
    pprint(completed)

    import matplotlib.pyplot as plt
    import networkx as nx

    labels = {}
    G = nx.DiGraph()
    for node in completed.values():
        labels[node] = str(type(node))
        if isinstance(node, EndNode):
            continue

        G.add_edge(node, node.next)

        if not isinstance(node, BranchNode):
            continue
        G.add_edge(node, node.alt)
    pos = nx.spring_layout(G)
    nx.draw(G, pos)
    nx.draw_networkx_labels(G, pos, labels, font_size=16)
    plt.show()

    print(completed[1])


print('Calling add_data via cffi')
# Interesting variation: passing invalid arguments to add_data will trigger
# a cffi type-checking exception.
dout = lib.regcomp(b"(a|b)+")
lib.regdump(dout)
parseProg(dout.program)
