# Test file for comments that overflow the 88 column line width. Those lines should be
# wrapped to the next line


class Abc(object):
    def b(self, c):
        # this is a normal comment that doesn't need wrapping
        self.d(c)

    def d(self, e):
        # this is an overly long comment that does need wrapping; it should be wrapped
        # to the next line
        self.b(e)

    def f(self):
        # here's an inline commend that should be moved to the line above
        return [self.b, self.d]
