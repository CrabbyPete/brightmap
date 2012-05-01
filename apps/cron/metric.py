import django_header

# Python imports
from datetime                       import  datetime

# Local imports
from google                         import  GoogleSpreadSheet
from base.models                    import  Chapter, Expire



SPREADSHEET = 'metric'
MONTH =  ['jan','feb','mar','apr','may','jun','jul','aug','sep','oct','nov','dec']

def open_spreadsheet( email, password ):
    """
    Open Google Docs and get the spreadsheet
    """
    
    spreadsheet = GoogleSpreadSheet( email, password )
    result = spreadsheet.getSpreadSheet(SPREADSHEET)
    if result == None or result.title.text != SPREADSHEET:
        print "Google Spreadsheet Error, Found: "  + result.title.text + \
              " Looking for: " + SPREADSHEET
        return None
    
    # Open the Organizers work sheet
    spreadsheet.getWorkSheet('Organizations')
    return spreadsheet


def count_deals(chapter, row):
    """
    Count the current number of deals
    """
 
    # Check the kind of deals/terms available for the chapter
    c_trials = 0
    c_standard = 0
    c_sponsored = 0
        
    # Count the current number of each type of deal
    deals = chapter.deals()
    for deal in deals:
        terms = deal.active()
        for term in terms:
            
            # Standard deals cost $20.
            if term.cost > 0:
                c_standard += 1
                
            # Sponsored deals are exclusive and free
            elif term.cost == 0 and term.exclusive:
                c_sponsored += 1
                
            # Count trials deals that have not expired
            else:
                if isinstance(term, Expire):
                    c_trials += 1
  
    row['sponsored']   = str(c_sponsored)
    row['paid']        = str(c_standard)
    row['trial']       = str(c_trials)


def count_attendees(chapter, row):
    """
    Count the attendees and connections
    """
    months = [0 for x in range(12)]
    
    total_connections = 0
    paid_connections  = 0
    total_attendees   = 0


    # Count for each event
    for event in chapter.events():
        attending = len( event.attendees() )
            
        if attending == 0:
            continue
                
        total_attendees += attending
        month = event.date.month - 1
            
        events = event.connections()
        for connect in events:
            total_connections += 1
            if connect.term.cost > 0 and connect.status == 'sent':
                paid_connections += 1
                months[month] += 1
   
        if total_attendees > 0: 
            ratio = float( paid_connections ) / float( total_attendees )
        else:
            ratio = 0.0
            
        total_events = len(events)
        if total_events > 0:
            aver  = float(total_attendees)/float(total_events)
            dollars = (float(paid_connections) * 20)/float(total_events)
        else:
            aver  = 0
            dollars = 0

    row['connections'] = str( total_connections ) 
    row['billable']    = str( paid_connections )
    row['events']      = str(total_events)
 
    row['attendees']   = "%.2f" % aver
    row['ratio']       = "%.2f" % ratio
    row['dollars']     = "%.2f" % dollars

    return months
    
    
def metric( email, password ):
    """
    Create a spreadsheet metrics of BrightMap activity
    """
    # Check each chapter
    chapters = Chapter.objects.all()
    
    # Open the spreadsheet and cells
    spreadsheet = open_spreadsheet( email, password )
    cells = spreadsheet.getCells()

    for chapter in chapters:
        
        # If there is no Eventbrite page forget it
        if not chapter.configured():
            continue
        
        row = dict()
        row ['date'] = datetime.today().strftime("%d/%m/%Y")
        row ['organization'] = chapter.name

        # Check the kind of deals/terms available for the chapter
        count_deals( chapter, row ) 

        # Count connections and attendees
        months = count_attendees( chapter, row )
        
        # Count each month
        for m,name in enumerate(MONTH): 
            row[name] = str( months[m] )
        
        found = False
        for index, cell in enumerate(cells):
            if 'organization' in cell and row['organization'] == cell['organization']:
                spreadsheet.editRow( index, row )
                found = True
                break
        if not found:
            spreadsheet.addRow( row )
        
    return

if __name__ == '__main__':
    metric( 'pete.douma@gmail.com','fishf00l'  )
