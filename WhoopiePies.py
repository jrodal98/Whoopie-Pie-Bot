from lxml import html
import urllib.request
import smtplib
import imaplib
import email
import re
import sys
import WhoopieConfig
"""
TODO:
2) Checks at the beginning of the week, so figure out how to make grabEachLocation() run once a week.
    - store the information so that it can be called on at any time (emailing daily reminders about the whoopie pie schedule)
        - delete sub-information when the day has passed already


"""

def whoopieGrabber(link,meal,location,pies):
    # whoopieGrabber searches through the Dessert section for the occurrence of a whoopie pie.
    try:
        page = urllib.request.urlopen(link).read() # gets the html page
    except Exception as e:
        errorMessage = 'Something went wrong with whoopieGrabber.  Here is the exception: '+str(e)
        checkErrorLog(errorMessage) # emails me the exception description

    days = {'Monday': '1', 'Tuesday': '2', 'Wednesday': '3', 'Thursday': '4', 'Friday': '5', 'Saturday': '6', 'Sunday': '7'}
    doc = html.fromstring(page) # prepares page to be read by the lxml module
    for day, code in days.items():
        column = "//div[@class='menu-details-day'][{}]".format(code)  # Looks at the menu for the specified day
        dessertStation = "/div[@class='menu-details-station'][4]"  # Looks at the menu for the dessert station
        dessertOptions = "//div[@class='menu-name']/a/text()"  # generates a list of all of the dessert items
        desserts = doc.xpath(column + dessertStation + dessertOptions)  # executes above commands
        for dessert in desserts:
            if 'whoopie' in dessert.lower():
                pies.append([dessert + 's', meal, location, day])


def grabEachLocation():
    # grabEachLocation runs whoopieGrabber for every meal at every dining hall.
    pies = []
    dining_halls = {"695": "O'Hill", "704": "Newcomb", "701": "Runk"} # Each Hall is associated with a location id
    id_meal = {'1422':'Brunch','1423':'Lunch','1424':'Dinner'} # each meal is associated with a period id
    for locationId, hall in dining_halls.items():
        for periodId, meal in id_meal.items():
            link = 'https://virginia.campusdish.com/Commerce/Catalog/Menus.aspx?LocationId={}&PeriodId={}&MenuDate=&Mode=week'.format(locationId,periodId)
            whoopieGrabber(link,meal,hall,pies) # gets dessert information for each combination of hall and meal
    return pies # returns list with desserts, meal time, location, and day.


def createMenu(pies):
    # createMenu creates a message to send to the email list.
    if len(pies) > 0:
        menu = 'According to the dining hall menus, this week\'s whoopie pie menu is as follows:\n'
        for result in pies:
            menu +='\n'+result[2]+' will be serving '+result[0]+' during '+result[1]+' on '+result[-1]+'.'
    else:
        menu = 'According to the dining hall menus, there won\'t be any whoopie pies this week :(\nYou will recieve an email if that changes.\n\n'
    return menu

def checkInbox():
    # checkInbox opens my email and returns a dictionary containing the email subject and a string with the email address buried.
    emailNameAndSubject = {}
    try:
        M = imaplib.IMAP4_SSL('imap.gmail.com')
        M.login(WhoopieConfig.BOT_EMAIL,WhoopieConfig.BOt_PASSWORD)
        M.select()
        type, data = M.search(None, 'ALL') # Looks at all emails
        for num in data[0].split():
            type, data = M.fetch(num, '(RFC822)')
            M.store(num,'+FLAGS','\\Deleted') # checks the delete box on the message
            for response in data:
                if isinstance(response, tuple):
                    message = email.message_from_bytes(response[1]) # looks at the email
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
    # Opens the saved email list
    emailList = []
    with open('WhoopiePieEmailList.txt') as f:
        for line in f.readlines():
            if line.strip() != '':
                emailList.append(line.strip())
    return emailList

def saveEmailList(emailList):
    # Saves email list
    with open('WhoopiePieEmailList.txt','w') as f:
        [print(email,file=f) for email in emailList]


def logIntoEmail():
    # Logs into my email (for sending emails).
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)  # Connects to server
        server.ehlo()  # Encryptes everything that follows
        server.starttls()
        server.login(WhoopieConfig.BOT_EMAIL, WhoopieConfig.BOt_PASSWORD)
        return server
    except:
        print('Failed to log into email.')
        sys.exit()

def logOutOfEmail(server):
    server.close()

def sendWelcomeEmail(server,email):
    # sends welcome email
    try:
        subject = 'You have been added to the UVA Whoopie Pie Email List'
        msg = 'Send an email to {} with the word "quit" in the subject header to be removed from this list.'.format(WhoopieConfig.BOT_EMAIL)
        message = 'Subject: {}\n\n{}'.format(subject, msg) # creates email
        server.sendmail(WhoopieConfig.BOT_EMAIL,email,message) # sends email
    except Exception as e:
        errorMessage = 'Something went wrong with sendWelcomeEmail.  Here is the exception: ' + str(e)
        checkErrorLog(errorMessage)

def sendGoodByeEmail(server,email):
    # sends goodbye mail
    try:
        subject = 'You have been removed from the UVA Whoopie Pie Email List'
        msg = 'Send an email to {} with the word "Whoopie Pie" in the subject header to rejoin.'.format(WhoopieConfig.BOT_EMAIL)
        message = 'Subject: {}\n\n{}'.format(subject, msg) # creates email
        server.sendmail(WhoopieConfig.BOT_EMAIL,email,message) # send email
    except Exception as e:
        errorMessage = 'Something went wrong with sendGoodByeEmail.  Here is the exception: ' + str(e)
        checkErrorLog(errorMessage)


def addOrRemoveFromEmailList(myInbox,emailList,server):
    # Adds or removes people from email list based on the subject of the emails in my inbox.
    for emailer, subject in myInbox.items():
        emailAddress = re.search('<([^>]+)>',emailer).group(1) # finds the email address from myInbox
        if emailAddress not in emailList:
            if 'pie' in subject.lower():
                emailList.append(emailAddress) # Adds the emailer to the list
                sendWelcomeEmail(server,emailAddress) # Sends the emailer a welcome email
        else:
            if 'quit' in subject.lower():
                emailList.remove(emailAddress) # removes emailer to the list
                sendGoodByeEmail(server,emailAddress) # sends the emailer a goodbye email



def sendMassEmail(server,msg,emailList):
    # sends the whoopie pie schedule to everyone on the email list.
    try:
        quitMessage = '\n\nSend {} an email with "Quit" in the subject header to be removed from this email list.'.format(WhoopieConfig.BOT_EMAIL)
        message = 'Subject: {}\n\n{}'.format('UVA Whoopie Pie Schedule', msg) # creates email
        for email in emailList:
            server.sendmail(WhoopieConfig.BOT_EMAIL, email, message+quitMessage) # sends email to each person one by one
    except Exception as e:
        errorMessage = 'Something went wrong with sendMassEmail.  Here is the exception: ' + str(e)
        checkErrorLog(errorMessage)

def checkErrorLog(errorMessage):
    # checks to see if an error is already in the error log
    with open('WhoopiePieErrors.txt','a+') as f:
        for line in f.readlines():
            if line.strip() == errorMessage:
                return True # returns true to indicate that the message is already in the error file.
        print(errorMessage,file=f) # Adds error message to error file if it hasn't already been added

def sendErrorEmail(server,errorMessage,sentMessages):
    # Sends an email to my personal email with a list of bugs to be fixed.
    subject = 'I have a bug that needs to be fixed.'
    message = 'Subject: {}\n\n{}'.format(subject, errorMessage)
    server.sendmail(WhoopieConfig.BOT_EMAIL,WhoopieConfig.PERSONAL_EMAIL,message)
    sentMessages.append(errorMessage) # adds email to a list of sent emails so that I don't send the same email over and over again.


def getSentMessages():
    # returns a list of sent emails
    with open('WhoopiePieSentErrors.txt') as f:
        errorMessages = []
        f.readline()
        for line in f.readlines():
            errorMessages.append(line.strip())
        return errorMessages



def getErrorMessages(server,sentMessages):
    # Sends error messages and then adds that email to the sent error messages file
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
