import bs4 as bs
import urllib.request
import smtplib
import imaplib
import email
import re
import sys

"""
TODO:
2) Checks at the beginning of the week, so figure out how to make grabEachLocation() run once a week.
    - store the information so that it can be called on at any time (emailing daily reminders about the whoopie pie schedule)
        - delete sub-information when the day has passed already

"""

def whoopieGrabber(link,meal,location,pies):
    try:
        sauce = urllib.request.urlopen(link).read()
    except Exception as e:
        errorMessage = 'Something went wrong with whoopieGrabber.  Here is the exception: '+str(e)
        checkErrorLog(errorMessage)

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
                            pies.append([dessert+'s', meal, location, betterDay[day]])

                    except:
                        dessert = item.span.string # gets items without links
                        if 'Whoopie' in dessert:
                            pies.append([dessert+'s', meal, location, betterDay[day]])



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
    return pies





def createMenu(pies):
    if len(pies) > 0:
        menu = 'According to the dining hall menus, this week\'s whoopie pie menu is as follows:\n'
        for result in pies:
            menu +='\n'+result[2]+' will be serving '+result[0]+' during '+result[1]+' on '+result[-1]+'.'
    else:
        menu = 'According to the dining hall menus, there won\'t be any whoopie pies this week :(\nYou will recieve an email if that changes.\n\n'
    return menu

def checkInbox():
    emailNameAndSubject = {}
    try:
        M = imaplib.IMAP4_SSL('imap.gmail.com')
        M.login('UVAWhoopiePie@gmail.com','WhoopiePiesAreGood!')
        M.select()
        type, data = M.search(None, 'ALL')
        for num in data[0].split():
            type, data = M.fetch(num, '(RFC822)')
            M.store(num,'+FLAGS','\\Deleted') # checks the delete box on the message
            for response in data:
                if isinstance(response, tuple):
                    message = email.message_from_bytes(response[1])
                    emailSubject = message['subject']
                    emailFrom = message['from']
                    emailNameAndSubject[emailFrom] = emailSubject
        M.expunge() # Deletes marked messages.
        M.close()
        M.logout()
    except Exception as e:
        errorMessage = 'Something went wrong with checkInbox.  Here is the exception: ' + str(e)
        checkErrorLog(errorMessage)
    return emailNameAndSubject

def getEmailList():
    emailList = []
    with open('WhoopiePieEmailList.txt') as f:
        for line in f.readlines():
            if line.strip() != '':
                emailList.append(line.strip())
    return emailList

def saveEmailList(emailList):
    with open('WhoopiePieEmailList.txt','w') as f:
        [print(email,file=f) for email in emailList]


def logIntoEmail():
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)  # Connects to server
        server.ehlo()  # Encryptes everything that follows
        server.starttls()
        server.login('UVAWhoopiePie@gmail.com', 'WhoopiePiesAreGood!')
        return server
    except:
        print('Failed to log into email.')
        sys.exit()

def logOutOfEmail(server):
    server.close()

def addOrRemoveFromEmailList(myInbox,emailList,server):
    for emailer, subject in myInbox.items():
        emailAddress = re.search('<([^>]+)>',emailer).group(1)
        if emailAddress not in emailList:
            if 'pie' in subject.lower():
                emailList.append(emailAddress)
                sendWelcomeEmail(server,emailAddress)
        else:
            if 'quit' in subject.lower():
                emailList.remove(emailAddress)
                sendGoodByeEmail(server,emailAddress)

def sendWelcomeEmail(server,email):
    try:
        subject = 'You have been added to the UVA Whoopie Pie Email List'
        msg = 'Send an email to UVAWhoopiePie@gmail.com with the word "quit" in the subject header to be removed from this list.'
        message = 'Subject: {}\n\n{}'.format(subject, msg)
        server.sendmail('UVAWhoopiePie@gmail.com',email,message)
    except Exception as e:
        errorMessage = 'Something went wrong with sendWelcomeEmail.  Here is the exception: ' + str(e)
        checkErrorLog(errorMessage)

def sendGoodByeEmail(server,email):
    try:
        subject = 'You have been removed from the UVA Whoopie Pie Email List'
        msg = 'Send an email to UVAWhoopiePie@gmail.com with the word "Whoopie Pie" in the subject header to rejoin.'
        message = 'Subject: {}\n\n{}'.format(subject, msg)
        server.sendmail('UVAWhoopiePie@gmail.com',email,message)
    except Exception as e:
        errorMessage = 'Something went wrong with sendGoodByeEmail.  Here is the exception: ' + str(e)
        checkErrorLog(errorMessage)

def sendMassEmail(server,msg,emailList):
    try:
        quitMessage = '\n\nSend UVAWhoopiePie@gmail.com an email with "Quit" in the subject header to be removed from this email list.'
        message = 'Subject: {}\n\n{}'.format('UVA Whoopie Pie Schedule', msg)
        for email in emailList:
            server.sendmail('UVAWhoopiePie@gmail.com', email, message+quitMessage)
    except Exception as e:
        errorMessage = 'Something went wrong with sendMassEmail.  Here is the exception: ' + str(e)
        checkErrorLog(errorMessage)

def checkErrorLog(errorMessage):
    with open('WhoopiePieErrors.txt','a+') as f:
        for line in f.readlines():
            if line.strip() == errorMessage:
                return True
        print(errorMessage,file=f)

def sendErrorEmail(server,errorMessage,sentMessages):
    subject = 'I have a bug that needs to be fixed.'
    message = 'Subject: {}\n\n{}'.format(subject, errorMessage)
    server.sendmail('UVAWhoopiePie@gmail.com','jr6ff@virginia.edu',message)
    sentMessages.append(errorMessage)


def getSentMessages():
    with open('WhoopiePieSentErrors.txt') as f:
        errorMessages = []
        f.readline()
        for line in f.readlines():
            errorMessages.append(line.strip())
        return errorMessages



def getErrorMessages(server,sentMessages):
    with open('WhoopiePieErrors.txt') as f:
        f.readline()
        for line in f.readlines():
            if line.strip() not in sentMessages:
                sendErrorEmail(server,line,sentMessages)
        with open('WhoopiePieSentErrors.txt','w') as f:
            print(0,file=f)
            [print(message,file=f) for message in sentMessages]

def main():
    server = logIntoEmail()
    pies = grabEachLocation()
    menu = createMenu(pies)
    emailList = getEmailList()
    myInbox = checkInbox()
    addOrRemoveFromEmailList(myInbox,emailList,server)
    sendMassEmail(server,menu,emailList)
    saveEmailList(emailList)
    sentErrorMessages = getSentMessages()
    getErrorMessages(server,sentErrorMessages)
    logOutOfEmail(server)
    print('done')

main()
