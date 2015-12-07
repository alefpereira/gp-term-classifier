from math import log

#linear =  lambda uti, maximo, parametro : uti * (parametro - 1) / maximo
def linear(uti, maximo, parametro, startsat = 0):
    if startsat < 0:
        raise ValueError('Argument startsat can not be negative.')
    result = 0.0
    try:
        result = uti * (parametro - 1) / maximo
    except ZeroDivisionError:
        result = 0.0

    # change the beginning of the numbers
    result += startsat
    return result

#return_linear =  lambda nlinear, maximo, parametro : nlinear * maximo / (parametro - 1)
def return_linear(nlinear, maximo, parametro, startsat = 0):
    if startsat < 0:
        raise ValueError('Argument startsat can not be negative.')

    #return to original beginning of the numbers
    nlinear -= startsat
    result = nlinear * maximo / (parametro - 1)
    return result

#lgrt = lambda uti, maximo, parametro :  log( (uti*(2**(parametro-1))/maximo) ,2)
def lgrt(uti, maximo, parametro, startsat = 0):
    if startsat < 0:
        raise ValueError('Argument startsat can not be negative.')
    result = 0.0
    try:
        result = log( (uti*(2**(parametro-1))/maximo) ,2)
    except ValueError:
        result = 0.0
    except ZeroDivisionError:
        result = 0.0

    if result < 0:
        result = 0.0

    # change the beginning of the numbers
    result += startsat
    return result

#return_lgrt = lambda nuti, maximo, parametro : (2**nlog) * maximo / 2**(parametro - 1)
def return_lgrt(nlog, maximo, parametro, startsat = 0):
    if startsat < 0:
        raise ValueError('Argument startsat can not be negative.')
    #return to original beginning of the numbers
    nlog -= startsat
    result = (2**nlog) * maximo / 2**(parametro - 1)
    return result

#exp = lambda uti, maximo, parametro:  2**(uti*log(parametro - 1,2)/maximo)
def exp(uti, maximo, parametro, startsat = 0):
    if startsat < 0:
        raise ValueError('Argument startsat can not be negative.')
    result = 0.0
    try:
        result = 2**(uti*log(parametro - 1,2)/maximo)
    except ZeroDivisionError:
        result = 0

    # change the beginning of the numbers
    result += startsat
    return result

#return_exp = lambda nexp, maximo, parametro : log(nexp, 2) * maximo / log(parametro - 1, 2)
def return_exp(nexp, maximo, parametro, startsat = 0):
    if startsat < 0:
        raise ValueError('Argument startsat can not be negative.')
    #return to original beginning of the numbers
    nexp -= startsat
    result = 0.0
    try:
        result = log(nexp, 2) * maximo / log(parametro - 1, 2)
    except ValueError:
        result = 0.0
    return result
