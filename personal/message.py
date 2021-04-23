def required_msg(field):
    return '{0} is required'.format(field)

def min_msg(field, minimum):
    return '{0} must be at least {1}'.format(field, minimum)

def minlen_msg(field, minimum):
    return '{0} required to be a minimum of {1} characters in length'.format(field, minimum)

def maxlen_msg(field, maximum):
    return '{0} exceeds maximum length of {1}'.format(field, maximum)

def get_error_list(dic={}):
    l = []
    for v in dic.values():
        for s in v:
            l.append(s)
            
    return l