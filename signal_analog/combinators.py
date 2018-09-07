"""Provides n-ary combinators for SignalFlow programs."""


class NAryCombinator(object):

    def __init__(self, operator, *ns):
        """N-ary combinator for SignalFlow objects.

        Arguments:
            operator: the operator to intersperse amongst expressions.
            ns: the expressions to compose.

        Returns:
            An object that can be serialized to SignalFlow.
        """
        if not operator:
            raise ValueError("Operator in NAryCombinator cannot be empty.")

        self.operator = operator
        self.stack = ns

    def __str__(self):
        args = []
        for item in self.stack:
            # Ensure that combining different combinators results in the
            # correct order of operations.
            if isinstance(item, NAryCombinator):
                args.append("(" + str(item) + ")")
            else:
                args.append(str(item))

        combinator = " {0} ".format(self.operator)
        return combinator.join(args)


class And(NAryCombinator):
    """And combinator for combining SignalFlow objects.
    """

    def __init__(self, *ns):
        super(And, self).__init__('and', *ns)


class Or(NAryCombinator):
    """Or combinator for combining SignalFlow objects.
    """

    def __init__(self, *ns):
        super(Or, self).__init__('or', *ns)


class Not(object):
    """Not combinator for performing nullification on SignalFlow objects.
    """

    def __init__(self, expr):
        """Negate the given expression.

        Arguments:
            expr: the expression to negate.

        Returns:
            An object that can be serialized to SignalFlow.
        """
        if not expr:
            raise ValueError("Expression cannot be empty in Not statement.")

        self.expr = expr

    def __str__(self):
        return "not " + str(self.expr)


class LT(NAryCombinator):
    """Less Than combinator for comparing SignalFlow objects.
    """

    def __init__(self, left, right):
        super(LT, self).__init__('<', left, right)


class GT(NAryCombinator):
    """Greater Than combinator for comparing SignalFlow objects.
    """

    def __init__(self, left, right):
        super(GT, self).__init__('>', left, right)


class LTE(NAryCombinator):

    def __init__(self, left, right):
        super(LTE, self).__init__('<=', left, right)


class GTE(NAryCombinator):

    def __init__(self, left, right):
        super(GTE, self).__init__('>=', left, right)


class Mul(NAryCombinator):
    """Multiplication combinator for performing math on SignalFlow objects.
    """

    def __init__(self, left, right):
        super(Mul, self).__init__('*', left, right)


class Div(NAryCombinator):
    """Division combinator for performing math on SignalFlow objects.
    """

    def __init__(self, left, right):
        super(Div, self).__init__('/', left, right)


class Add(NAryCombinator):
    """Addition combinator for performing math on SignalFlow objects.
    """

    def __init__(self, left, right):
        super(Add, self).__init__('+', left, right)


class Sub(NAryCombinator):
    """Subtraction combinator for performing math on SignalFlow objects.
    """

    def __init__(self, left, right):
        super(Sub, self).__init__('-', left, right)
