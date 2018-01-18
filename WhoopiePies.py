import bs4 as bs
import urllib.request


"""
TODO:
1) Take the information from the pies list and display it nicely.
2) Checks at the beginning of the week, so figure out how to make grabEachLocation() run once a week.
    - store the information so that it can be called on at any time (emailing daily reminders about the whoopie pie schedule)
        - delete sub-information when the day has passed already
3) Send the information via email using a bot
    - Emailing the bot should add a user to the email list
    - Daily emails + new users get an email immediately
"""

def whoopieGrabber(link,meal,location,pies):
    sauce = urllib.request.urlopen(link).read()
    soup = bs.BeautifulSoup(sauce, 'lxml')
    betterDay = {'Mon':'Monday','Tue':'Tuesday','Wed':'Wednesday','Thu':'Thursday','Fri':'Friday','Sat':'Saturday','Sun':'Sunday'}
    for column in soup.find_all('div', class_='menu-details-day'): # Looks at each day
        day = column.h2.string
        for station in column.find_all('div',class_='menu-details-station'): # Looks at each station
            if station.h4.string == 'Dessert' :
                for item in station.find_all('div',class_='menu-name'): # Looks at each item served at the dessert station
                    try: # gets items with links;
                        dessert = item.a.string
                        if 'Whoopie' in dessert:
                            pies.append('|'.join([dessert,meal,location,betterDay[day]]))

                    except:
                        dessert = item.span.string # gets items without links
                        if 'Whoopie' in dessert:
                            pies.append('|'.join([dessert,meal,location,betterDay[day]]))



def grabEachLocation():
    pies = []
    dining_halls = {"695": "O'Hill", "704": "Newcomb", "701": "Runk"}
    id_meal = {'1422':'Brunch','1423':'Lunch','1424':'Dinner'}
    for locationId, hall in dining_halls.items():
        for periodId, meal in id_meal.items():
            whoopieGrabber('https://virginia.campusdish.com/Commerce/Catalog/Menus.aspx?LocationId='+locationId+'&PeriodId='+periodId+'&MenuDate=&Mode=week',
                           meal,
                           hall,
                           pies)
    print(pies)

grabEachLocation()