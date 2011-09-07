from random import choice

def generate(length):
    """Make a password.

    Password length is an argument. Which characters are used can be set below.
    """
    # Define character classes.
    az = range(ord('a'),ord('z')+1)
    AZ = range(ord('A'),ord('Z')+1)
    zero_to_9 = range(ord('0'),ord('9')+1)
    special = [ord(x) for x in '!@#$%^&*']
    # special = [ord(x) for x in '!@#$%^&*()-_=+[]{};:,.<>/?\|`~']
    # Select character classes to use.
    # Special characters may not be valid on the system where you want to use
    # these passwords! They are therefore not used by default. Modify the string
    # on the line below accordingly, and probably also the 'special' list
    # above.
    characters = az + AZ + zero_to_9 #+ special
    pw = ''
    for i in range(length):
        pw += chr(choice(characters))
    return pw


def gen(alpha=6,numeric=2):
    """
    returns a human-readble password (say rol86din instead of
    a difficult to remember K8Yn9muL )
    """
    import string
    import random
    vowels = ['a','e','i','o','u']
    consonants = [a for a in string.ascii_lowercase if a not in vowels]
    digits = string.digits

    ####utility functions
    def a_part(slen):
        ret = ''
        for i in range(slen):
            if i%2 ==0:
                randid = random.randint(0,20) #number of consonants
                ret += consonants[randid]
            else:
                randid = random.randint(0,4) #number of vowels
                ret += vowels[randid]
        return ret

    def n_part(slen):
        ret = ''
        for i in range(slen):
            randid = random.randint(0,9) #number of digits
            ret += digits[randid]
        return ret

    ####
    fpl = alpha/2
    if alpha % 2 :
        fpl = int(alpha/2) + 1
    lpl = alpha - fpl

    start = a_part(fpl)
    mid = n_part(numeric)
    end = a_part(lpl)

    return "%s%s%s" % (start,mid,end)
