"""Provides n-ary combinators for SignalFlow programs."""


class BinaryCombinator(object):

    def __init__(self, operator, *ns):
        """Binary combinator for SignalFlow objects.

        Arguments:
            operator: the operator to intersperse amongst expressions.
            ns: the expressions to compose.

        Returns:
            An object that can be serialized to SignalFlow.
        """
        if not operator:
            raise ValueError("Operator in BinaryCombinator cannot be empty.")

        self.operator = operator
        self.stack = ns

    def __str__(self):
        combinator = " {0} ".format(self.operator)
        return combinator.join(map(str, self.stack))


class And(BinaryCombinator):

    def __init__(self, *ns):
        super(And, self).__init__('and', *ns)


class Or(BinaryCombinator):

    def __init__(self, *ns):
        super(Or, self).__init__('or', *ns)


class Not(object):

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
