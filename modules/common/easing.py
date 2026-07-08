from math import pow, sqrt, sin, cos, pi


c1 = 1.70158
c2 = c1 * 1.525
c3 = c1 + 1
c4 = (2 * pi) / 3
c5 = (2 * pi) / 4.5


def linear(x):
    return x


def easeInQuad(x):
    return x * x


def easeOutQuad(x):
    return 1 - (1 - x) * (1 - x)


def easeInOutQuad(x):
    if x < 0.5:
        return 2 * x * x

    return 1 - pow(-2 * x + 2, 2) / 2


def easeInCubic(x):
    return x * x * x


def easeOutCubic(x):
    return 1 - pow(1 - x, 3)


def easeInOutCubic(x):
    return 4 * x * x * x if x < 0.5 else 1 - pow(-2 * x + 2, 3) / 2


def easeInQuart(x):
    return x * x * x * x


def easeOutQuart(x):
    return 1 - pow(1 - x, 4)


def easeInOutQuart(x):
    return 8 * x * x * x * x if x < 0.5 else 1 - pow(-2 * x + 2, 4) / 2


def easeInQuint(x):
    return x * x * x * x * x


def easeOutQuint(x):
    return 1 - pow(1 - x, 5)


def easeInOutQuint(x):
    if x < 0.5:
        return 16 * x * x * x * x * x

    return 1 - pow(-2 * x + 2, 5) / 2


def easeInSine(x):
    return 1 - cos((x * pi) / 2)


def easeOutSine(x):
    return sin((x * pi) / 2)


def easeInOutSine(x):
    return -(cos(pi * x) - 1) / 2


def easeInExpo(x):
    return 0 if x == 0 else pow(2, 10 * x - 10)


def easeOutExpo(x):
    return 1 if x == 1 else 1 - pow(2, -10 * x)


def easeInOutExpo(x):
    if x in (0, 1):
        return x

    if x < 0.5:
        return pow(2, 20 * x - 10) / 2

    return (2 - pow(2, -20 * x + 10)) / 2


def easeInCirc(x):
    return 1 - sqrt(1 - pow(x, 2))


def easeOutCirc(x):
    return sqrt(1 - pow(x - 1, 2))


def easeInOutCirc(x):
    if x < 0.5:
        return (1 - sqrt(1 - pow(2 * x, 2))) / 2

    return (sqrt(1 - pow(-2 * x + 2, 2)) + 1) / 2


def easeInBack(x):
    return c3 * x * x * x - c1 * x * x


def easeOutBack(x):
    return 1 + c3 * pow(x - 1, 3) + c1 * pow(x - 1, 2)


def easeInOutBack(x):
    if x < 0.5:
        return (pow(2 * x, 2) * ((c2 + 1) * 2 * x - c2)) / 2

    return (pow(2 * x - 2, 2) * ((c2 + 1) * (x * 2 - 2) + c2) + 2) / 2


def easeInElastic(x):
    if x in (0, 1):
        return x

    return  -pow(2, 10 * x - 10) * sin((x * 10 - 10.75) * c4)


def easeOutElastic(x):
    if x in (0, 1):
        return x

    return pow(2, -10 * x) * sin((x * 10 - 0.75) * c4) + 1


def easeInOutElastic(x):
    if x in (0, 1):
        return x

    if x < 0.5:
        return -(pow(2, 20 * x - 10) * sin((20 * x - 11.125) * c5)) / 2

    return  (pow(2, -20 * x + 10) * sin((20 * x - 11.125) * c5)) / 2 + 1


def easeInBounce(x):
    return 1 - easeOutBounce(1 - x)


def easeOutBounce(x):
    n1 = 7.5625
    d1 = 2.75

    if x < 1 / d1:
        return n1 * x * x

    if x < 2 / d1:
        x -= 1.5 / d1
        return n1 * x * x + 0.75

    if x < 2.5 / d1:
        x -= 2.25 / d1
        return n1 * x * x + 0.9375

    x -= 2.625 / d1
    return n1 * x * x + 0.984375


def easeInOutBounce(x):
    if x < 0.5:
        return (1 - easeOutBounce(1 - 2 * x)) / 2

    return (1 + easeOutBounce(2 * x - 1)) / 2
