import re

from geo    import geocode


#'"APT","APARTMENT","BLDG","BUILDING","DEPT","DEPARTMENT","FL","FLOOR","HNGR","HANGER","LOT","PIER","RM","ROOM","TRLR","TRAILER","UNIT","SUITE","STE"'
regex_suba  = "(APT|APARTMENT|BLDG|BUILDING|DEPT|DEPARTMENT|FL|FLOOR|HNGR|HANGER|LOT|PIER|RM|ROOM|TRLR|TRAILER|UNIT|SUITE|STE|BOX)"
regex_pob = "((P\.O\. BOX)|(PO BOX)|(POBOX)|(P O BOX))"

def parse_address(address):
    """
    Authorize.net address verification does not care about sub address and po boxs should be
    # PO Box format eg 123 PO Box
    """
    po   = re.compile(regex_pob,  re.I)
    found = po.search(address)
    if found:
        where = address.find(found.group(0))
        a2 = address[where:]
        n = re.sub("\D", "", a2)
        a2 = a2.replace(n,"")
        a2 = n+' '+a2
        return a2
    else:
        subs = re.compile(regex_suba, re.I)
        found = subs.search(address)
        if found:
            where = address.find(found.group(0))
            return address[0:where]


def validate_address(street, city, state, zipcode):
    """
    Validate an address with Google
    """
    # Look for any sub addresses like Apt, Building .. and dump them
    sub_address = parse_address( street )
    if sub_address and sub_address != street:
        address = sub_address
    else:
        address = street
            
    address += " " + city + " " + state + " " + zipcode
    try:
        local = geocode(address)
    except Exception, e:
        return None
                
    return local