import requests, json, time, os, sys, random
from datetime import date, timedelta
from Classes.discord_hooks import Webhook
from Classes.logger import Logger
from pathlib import Path
from threading import Thread
from random import randint

class SelfridgesBookingCheckout:
    def __init__(self, profileJson, profileIndex=None, proxy=None, data=None):

        #self.jsonIndex = profileIndex
        self.proxy = proxy #Singular proxy, define the proxy json beforehand
        self.dayIncrease = 0
        self.timeslotTries = 0 

        #Extract Profile Data
        self.profileJson = profileJson
        self.ProfileName = self.profileJson["ProfileName"]
        self.firstName = self.profileJson["First Name"]
        self.lastName = self.profileJson["Last Name"]
        self.Email = self.profileJson["Email"]
        self.Phone = self.profileJson["Phone"]
        self.Instagram = self.profileJson["Instagram"]
        self.timePreferences = self.profileJson["Time Preferences"]
        self.nikeSize = self.profileJson["Nike Size"]
        self.adidasSize = self.profileJson["Adidas Size"]
        self.shirtSize = self.profileJson["Shirt Size"]
        self.trouserSize = self.profileJson["Trouser Size"]
        self.brandChoices = self.profileJson["TYD What stores?"]

        logPath = f"Logs/Selfridges/Bookings/{self.ProfileName}/"
        Path(logPath).mkdir(parents=True, exist_ok=True)

        self.fileDir = logPath + "/checkout.log"

        if data == None:
            self.storeID = self.profileJson["Store ID"]
            self.serviceID = self.profileJson["Service ID"]
            self.duration = self.profileJson["Event Duration"]
        else:
            self.eventName = data["Event Name"]
            self.storeID = data["Store ID"]
            self.serviceID = data["Service ID"]
            self.duration = data["Booking Timestep"]
            self.eventDescription = data["Event Description"]
            self.questionData = data["Question Data"]
        
        if self.storeID == "37463":
            self.storeName = "The Yellow Drop"
            self.storeImage = "https://images.selfridges.com/is/image/selfridges/2103_TYDS_LOGO?qlt=100&fmt=jpg&scl=1"
        
        elif self.storeID == "37453":
            self.storeName = "Offspring"
            self.storeImage = "https://images.selfridges.com/is/image/selfridges/2104_APPT_OFFSPRING?qlt=100&fmt=jpg&scl=1"
        
        elif self.storeID == "37250":
            self.storeName = "Aqua Di Parma"
            self.storeImage = "http://images.selfridges.com/is/image/selfridges/ACD_BOOKING?qlt=80&fmt=jpg&scl=1"

        elif self.storeID == "37331":
            self.storeName = "Selfridges Bookings"
            self.storeImage = "https://bookings.selfridges.com/selfridges-body-denim/images/selfridges-logo.png"

        elif self.storeID == "37510":
            self.storeName = "Wonder Room"
            self.storeImage = "https://bookings.selfridges.com/selfridges-body-denim/images/selfridges-logo.png"
        else:
            self.storeName = f"Selfridges Bookings | Store ID: {self.storeID}"
            self.storeImage = "https://bookings.selfridges.com/selfridges-body-denim/images/selfridges-logo.png"

            
        
        self.eventURL = f"https://bookings.selfridges.com/selfridges-body-denim/new_booking.html?companyId={self.storeID}"

    def timesIndex(self):
        self.SuitableTimeRanges = []
        for timePrefRange in self.timePreferences:
            times = {
                "10-11": "600-660",
                "11-12": "660-720",
                "12-13": "720-780",
                "13-14": "780-840",
                "14-15": "840-900",
                "15-16": "900-960",
                "16-17": "960-1020",
                "17-18": "1020-1080",
                "18-19": "1080-1140",
                "19-20": "1140-1200",
                "20-21": "1200-1260",
                "21-22": "1260-1320",
                "ALL": "60-1440",
                "":"60-1440",
            }
            timeidRange = times[timePrefRange]
            self.SuitableTimeRanges.append(timeidRange)
        return self.SuitableTimeRanges
    
    def createSession(self):
        self.s = requests.session()
        if self.proxy == None:
            pass
        else:
            self.s.proxies.update(self.proxy)    
    
    def getEventTimes(self):
        log = Logger(f"Event Times {self.storeID}| {self.ProfileName}").log
        gottenEventTimes = False
        while gottenEventTimes == False:
            try:
                startDate = (date.today() + timedelta(days=self.dayIncrease))
                endDate = (startDate + timedelta(days=7))
                log(f"{startDate} {endDate}", file=self.fileDir, messagePrint=False)
                url = f"https://selfridges.bookingbug.com/api/v1/{self.storeID}/time_data?service_id={self.serviceID}&date={startDate}&end_date={endDate}&duration={self.duration}"
                log("Sending get request for event times using URL: {url}", file=self.fileDir, messagePrint=False)
                headers = {
                    'Connection': 'keep-alive',
                    'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="90", "Google Chrome";v="90"',
                    'Accept': 'application/hal+json,application/json',
                    'App-Id': 'f6b16c23',
                    'App-Key': 'f0bc4f65f4fbfe7b4b3b7264b655f5eb',
                    'sec-ch-ua-mobile': '?0',
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
                    'Origin': 'https://bookings.selfridges.com',
                    'Referer': 'https://bookings.selfridges.com/',
                    'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8', 
                }
                response = self.s.get(url, headers=headers, allow_redirects=False, timeout=45)
                if 200 <= response.status_code <= 299:
                    log("Get request for event times successfully sent!", file=self.fileDir, messagePrint=False)
                    jsonData = json.loads(response.text)
                    self.eventTimeSlots = []
                    data = jsonData["_embedded"]["events"]
                    for i in data:
                        dayTimeSlots = i["times"]
                        eventDate = i["date"]
                        eventID = i["event_id"]
                        eventName = i["name"]
                        for timeSlot in dayTimeSlots:
                            slotTimeNumber = timeSlot["time"]
                            slotDateime = timeSlot["datetime"]
                            timedata = {
                                "Event Name": eventName,
                                "Event ID": eventID,
                                "Event Date": eventDate,
                                "slotDate": slotDateime,
                                "slotTimeNumber": slotTimeNumber,
                            }
                            self.eventTimeSlots.append(timedata)
                    
                    if self.eventTimeSlots != []:
                        gottenEventTimes = True 
                        log(f"Received event times:\n{self.eventTimeSlots}", color="blue", file=self.fileDir, messagePrint=False)
                        return self.eventTimeSlots
                    else:
                        log(f"No event times founds retrying...:\n{self.eventTimeSlots}", color="magenta", file=self.fileDir, messagePrint=False)
                        continue
                
                elif 400 <= response.status_code <= 499:
                    jsonData = json.loads(response.text)
                    if jsonData["error"] == "No bookable events found":
                        log(f"No timeslots loaded...", file=self.fileDir, messagePrint=True)
                    else:
                        log(f"Unknown 4xx error: {response.status_code} | {response.text} ", file=self.fileDir, messagePrint=True)
                    continue

                elif 500 <= response.status_code <= 599:
                    log(f"Retrying getting event times: {response.status_code}", color='magenta', file=self.fileDir, messagePrint=True)
                    continue
                
                else:
                    log(f"Unknown error get event times: {response.status_code}", color="magenta", file=self.fileDir, messagePrint=False)
                    continue
        
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                filename = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                log("{}, {}, {}, {} - {}".format(exc_type, exc_tb.tb_lineno, exc_obj, filename, e), file=self.fileDir, messagePrint=True) 
    
    def suitableTimeSlot(self):  
        log = Logger(f"Suitable Time Slot | {self.ProfileName}").log         
        gotSuitableTime = False
        while gotSuitableTime == False:
            try:
                log("Selecting timeslot...", color='yellow', file=self.fileDir, messagePrint=True)
                timeSlotData = self.eventTimeSlots.pop(0)
            except IndexError as e:
                self.getEventTimes()
                timeSlotData = self.eventTimeSlots.pop(0)
            try:
                eventSlotTimeNumber = int(timeSlotData["slotTimeNumber"])
                if self.timeslotTries <= 14:
                    for i in self.SuitableTimeRanges:
                        min = int(i.split("-")[0])
                        max = int(i.split("-")[1])
                        if min <= eventSlotTimeNumber <= max:
                            log(f"Time slot selected! Preferences matched!: {eventSlotTimeNumber}", color='yellow', file=self.fileDir, messagePrint=True)
                            gotSuitableTime = True
                            return timeSlotData
                        else:
                            log(f"Time slot DOES NOT match preferrences!: {eventSlotTimeNumber}", color='magenta', file=self.fileDir, messagePrint=True)
                    
                    self.timeslotTries += 1
                else:
                    log(f"No preferences matched after 15 tries, selecting first available time!: {eventSlotTimeNumber}", color='yellow', file=self.fileDir, messagePrint=True)
                    gotSuitableTime = True
                    return timeSlotData
                    
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                filename = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                log("{}, {}, {}, {} - {}".format(exc_type, exc_tb.tb_lineno, exc_obj, filename, e), file=self.fileDir, messagePrint=True)       
    
    def cartTimeSlot(self):
        log = Logger(f"Cart Time Slot | {self.ProfileName}").log
        cartSuccessful = False
        while cartSuccessful == False:
            try:
                timeSlotData = self.suitableTimeSlot()
                self.eventSlotTimeNumber = int(timeSlotData["slotTimeNumber"])
                self.eventID = timeSlotData["Event ID"]
                self.eventDate = timeSlotData["Event Date"]
                self.eventSlotDate = timeSlotData["slotDate"].replace("+", ".000Z").split("Z")[0] + "Z"
                self.referenceID = f"10{random.randint(11111111, 99999999)}"

                headers = {
                    'Host': 'selfridges.bookingbug.com',
                    'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="90", "Google Chrome";v="90"',
                    'Accept': 'application/hal+json,application/json',
                    'App-Id': 'f6b16c23',
                    'App-Key': 'f0bc4f65f4fbfe7b4b3b7264b655f5eb',
                    'sec-ch-ua-mobile': '?0',
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
                    'Content-Type': 'application/json',
                    'Origin': 'https://bookings.selfridges.com',
                    'Referer': 'https://bookings.selfridges.com/',
                    'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
                }
                params = (
                    ('service_id', self.serviceID),
                )
                data = {
                    "entire_basket": True,
                    "items":[
                    {
                        "date": self.eventDate,
                        "time": self.eventSlotTimeNumber,
                        "event_id": self.eventID,
                        "price": None,
                        "book":f"https://selfridges.bookingbug.com/api/v1/{self.storeID}/basket/add_item?service_id={self.serviceID}",
                        "duration": self.duration,
                        "settings": {
                            "resource":-1,
                            "person":-1,
                            "earliest_time": self.eventSlotDate
                            },
                            "service_id": self.serviceID,
                            "ref": int(self.referenceID)
                        }
                    ]
                }
                dataMetric = json.dumps(data, separators=(',', ':'))
                response = self.s.post(f'https://selfridges.bookingbug.com/api/v1/{self.storeID}/basket/add_item', headers=headers, params=params, data=dataMetric)
                log(response.request.body, color="yellow", file="Logs/Bookings", messagePrint=False)
                if response.status_code == 201 or response.status_code == '201':
                   
                    self.authTokenHeader = response.headers["Auth-Token"]
                    self.uidTokenHeader = response.headers["uid"]

                    #print(self.authTokenHeader, self.uidTokenHeader)
                    #log(response.headers, file=self.fileDir, messagePrint=True)

                    jsonData = json.loads(response.text)
                    try:
                        if jsonData["_embedded"]["items"][0]["ref"] == int(self.referenceID) or jsonData["_embedded"]["items"][0]["ref"] == self.referenceID:
                            log(f"Succesfully added slot time to cart: {self.eventName} at {self.eventSlotDate}", color='green', file=self.fileDir, messagePrint=True)
                            responsedata = jsonData["_embedded"]["items"][0]
                            self.checkoutID = responsedata["id"]
                            self.personID = responsedata["person_id"]
                            self.resourceID = responsedata["resource_id"]
                            self.status = responsedata["status"]
                            self.earliestTime = responsedata["settings"]["earliest_time"]
                            cartSuccessful = True 

                    except IndexError or KeyError as e:
                        log(f"Unsucessfully added to cart: {self.eventName} at {self.eventSlotDate} {self.eventSlotDate}", color='red', file=self.fileDir, messagePrint=True)
                
                elif response.status_code == 409 or response.status_code == '409':
                    jsonData = json.loads(response.text)
                    if jsonData["error"] == 'No Space Left':
                        log("Time slot unavailable, selecting new time slot...", color='magenta', file=self.fileDir, messagePrint=True)
                        self.getEventTimes()
                        continue

                    elif jsonData["error"] == 'Min advance time passed':
                        log("Can't checkout... Time slot too soon, selecting new time slot", color='magenta', file=self.fileDir, messagePrint=True)
                        self.dayIncrease = 2
                        self.getEventTimes()
                        continue

                elif 500 <= response.status_code <= 599:
                    log(f"Retrying adding slot to cart: {response.status_code}", color='magenta', file=self.fileDir, messagePrint=True)
                    continue
    
                else:
                    log(f"{response.status_code}, {response.text}", color='red', file=self.fileDir, messagePrint=True)

            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                filename = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                log("{}, {}, {}, {} - {}".format(exc_type, exc_tb.tb_lineno, exc_obj, filename, e), file=self.fileDir, messagePrint=True)  
    
    def setCheckoutInfo(self):
        log = Logger(f"Checkout Info | {self.ProfileName}").log
        try:
            #log(self.questionData, color='blue', file=self.fileDir, messagePrint=True)
            questionForm = []
            discordData = []
            for index, i in enumerate(self.questionData):
                log(i, color='blue', file=self.fileDir, messagePrint=True)
                try:
                    if i["type"] == "heading":
                        question = {
                            "id": i["id"]
                        }
                        discordInfo = {
                            "name": i["name"],
                            "answer": ""
                        }
                        questionForm.append(question)
                        discordData.append(discordInfo)

                except KeyError as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    filename = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    log("{}, {}, {}, {} - {}".format(exc_type, exc_tb.tb_lineno, exc_obj, filename, e), file=self.fileDir, messagePrint=False)
                    pass 
                
                try:
                    if i["type"] == "check": 
                        question = {
                            "id": i["id"],
                            "answer": True
                        }
                        discordInfo = {
                            "name": i["name"],
                            "answer": True
                        }
                
                        questionForm.append(question)
                        discordData.append(discordInfo)
                    
                except KeyError as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    filename = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    log("{}, {}, {}, {} - {}".format(exc_type, exc_tb.tb_lineno, exc_obj, filename, e), file=self.fileDir, messagePrint=False)
                    pass 
                try:
                    if i["type"] == "select":
                        if 'top size' in i["name"].lower():
                            for key in i["options"]:
                                for k in key.keys():
                                    if k == self.shirtSize:
                                        question = {
                                            "id": self.questionData[index]["id"],
                                            "answer": k
                                        }
                                        discordInfo = {
                                            "name": self.questionData[index]["name"],
                                            "answer": k
                                        }
                                        questionForm.append(question)
                                        discordData.append(discordInfo)
                                        break
                        

                        elif 'bottom size' in i["name"].lower():
                            for key in i["options"]:
                                for k in key.keys():
                                    if k == self.trouserSize:
                                        question = {
                                            "id": self.questionData[index]["id"],
                                            "answer": k
                                        }
                                        discordInfo = {
                                            "name": self.questionData[index]["name"],
                                            "answer": k
                                        }
                                        questionForm.append(question)
                                        discordData.append(discordInfo)
                                        break

                        elif 'nike' in i["name"].lower():
                           for key in i["options"]:
                                for k in key.keys():
                                    if k in self.nikeSize:
                                        question = {
                                            "id": self.questionData[index]["id"],
                                            "answer": k
                                        }
                                        discordInfo = {
                                            "name": self.questionData[index]["name"],
                                            "answer": k
                                        }
                                        questionForm.append(question)
                                        discordData.append(discordInfo)
                                        break
                        elif 'adidas' in i["name"].lower():
                            for key in i["options"]:
                                for k in key.keys():
                                    if k in self.adidasSize:
                                        question = {
                                            "id": self.questionData[index]["id"],
                                            "answer": k
                                        }
                                        discordInfo = {
                                            "name": self.questionData[index]["name"],
                                            "answer": k
                                        }
                                        questionForm.append(question)
                                        discordData.append(discordInfo)
                                        break

                        elif 'preferred platform' in i["name"].lower():
                            for key in i["options"]:
                                for k in key.keys():
                                    if 'skype' in k.lower():
                                        question = {
                                            "id": self.questionData[index]["id"],
                                            "answer": k
                                        }
                                        discordInfo = {
                                            "name": self.questionData[index]["name"],
                                            
                                            "answer": k
                                        }
                                        questionForm.append(question)
                                        discordData.append(discordInfo)
                                        break
                        
                        else:
                            for key in i["options"]:
                                key = random.choice(i["options"])
                                k = list(key.keys())[0]
                                question = {
                                    "id": self.questionData[index]["id"],
                                    "answer": k
                                }
                                discordInfo = {
                                    "name": self.questionData[index]["name"],
                                    "answer": k
                                }
                                questionForm.append(question)
                                discordData.append(discordInfo)
                                break
                        

                except KeyError as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    filename = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    log("{}, {}, {}, {} - {}".format(exc_type, exc_tb.tb_lineno, exc_obj, filename, e), file=self.fileDir, messagePrint=False)
                    pass 
                
                try:
                    if i["type"] == "text_field":
                        if 'brand' in i["name"].lower():
                            question = {
                                "id": i["id"],
                                "answer": self.brandChoices,
                            }
                            discordInfo = {
                                "name": i["name"],
                                "answer": self.brandChoices
                            }
                            questionForm.append(question)
                            discordData.append(discordInfo)
                            
                        elif 'instagram' in i["name"].lower():
                            question = {
                                "id": i["id"],
                                "answer": self.Instagram
                            }
                            discordInfo = {
                                "name": i["name"],
                                "answer": self.Instagram
                            }
                            questionForm.append(question)
                            discordData.append(discordInfo)

                        elif 'arrival' in i["name"].lower():
                            question = {
                                "id": i["id"],
                                "answer": "n/a"
                            }
                            discordInfo = {
                                "name": i["name"],
                                "answer": "n/a"
                            }
                            questionForm.append(question)
                            discordData.append(discordInfo)
                        elif 'nike' in i["name"].lower():
                            question = {
                                "id": i["id"],
                                "answer": self.nikeSize
                            }
                            discordInfo = {
                                "name": i["name"],
                                "answer": self.nikeSize
                            }
                            questionForm.append(question)
                            discordData.append(discordInfo)
                        
                        elif 'adidas' in i["name"].lower():
                            question = {
                                "id": i["id"],
                                "answer": self.adidasSize
                            }
                            discordInfo = {
                                "name": i["name"],
                                "answer": self.adidasSize
                            }
                            questionForm.append(question)
                            discordData.append(discordInfo)
                        elif 'pre-consultation' in i["name"].lower():
                            question = {
                                "id": i["id"],
                                "answer": "ASAP"
                            }
                            discordInfo = {
                                "name": i["name"],
                                "answer": "ASAP"
                            }
                            questionForm.append(question)
                            discordData.append(discordInfo)
                        else:
                            question = {
                                "id": i["id"],
                                "answer": "n/a"
                            }
                            discordInfo = {
                                "name": i["name"],
                                "answer": "n/a"
                            }
                            questionForm.append(question)
                            discordData.append(discordInfo)
                            
                except KeyError as e:
                    exc_type, exc_obj, exc_tb = sys.exc_info()
                    filename = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                    log("{}, {}, {}, {} - {}".format(exc_type, exc_tb.tb_lineno, exc_obj, filename, e), file=self.fileDir, messagePrint=False)
                    pass 
        
            
            self.questionForm = questionForm
            log(self.questionForm, file=self.fileDir, messagePrint=True)
            self.discordData = discordData
            log(self.discordData, file=self.fileDir, messagePrint=False)

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            filename = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            log("{}, {}, {}, {} - {}".format(exc_type, exc_tb.tb_lineno, exc_obj, filename, e), file=self.fileDir, messagePrint=True) 
    
    def updatePersonalData(self):
        log = Logger(f"Personal Data | {self.ProfileName}").log
        updatedPersonalData = False
        while updatedPersonalData == False:
            try:
                headers = {
                    'Host': 'selfridges.bookingbug.com',
                    'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="90", "Google Chrome";v="90"',
                    'App-Key': 'f0bc4f65f4fbfe7b4b3b7264b655f5eb',
                    'sec-ch-ua-mobile': '?0',
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
                    'Content-Type': 'application/json',
                    'Accept': 'application/hal+json,application/json',
                    'App-Id': 'f6b16c23',
                    'Auth-Token': self.authTokenHeader,
                    'Origin': 'https://bookings.selfridges.com',
                    'Referer': 'https://bookings.selfridges.com/',
                    'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
                }

                data = {
                    "consent":True,
                    "first_name":self.firstName,
                    "last_name":self.lastName,
                    "email":self.Email,
                    "default_company_id":self.storeID,
                    "mobile":self.Phone,
                    "questions":[],
                    "extra_info":
                    {
                        "locale":"en"
                    }
                }
                dataMetric = json.dumps(data, separators=(',', ':'))
                response = self.s.post(f'https://selfridges.bookingbug.com/api/v1/{self.storeID}/client', headers=headers, data=dataMetric, timeout=45)
                log(response.request.body, color="yellow", file="Logs/Bookings", messagePrint=False)
                if response.status_code == 201 or response.status_code == '201':
                    jsonData = json.loads(response.text)
                    try:
                        if jsonData["email"] == self.Email:
                            log("Succesfully added profile as a client!", color='green', file=self.fileDir, messagePrint=True)
                            self.profileID = jsonData["id"]
                            self.mobileNoPrefix = jsonData["mobile"]
                            self.mobilePrefix = jsonData["mobile_prefix"]

                            log(f"Succesfully received profileID: {self.profileID}", color='yellow', file=self.fileDir, messagePrint=True)
                            updatedPersonalData = True 

                    except IndexError or KeyError as e:
                        log(f"Unsucessfully added profile as a client...", color='red', file=self.fileDir, messagePrint=True)
                
                elif 500 <= response.status_code <= 599:
                    log(f"Retrying adding profile as a client: {response.status_code}", color='magenta', file=self.fileDir, messagePrint=True)
                    continue

                else:
                    log(f"{response.status_code}\n {response.text}", color='red', file=self.fileDir, messagePrint=True)
                
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                filename = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                log("{}, {}, {}, {} - {}".format(exc_type, exc_tb.tb_lineno, exc_obj, filename, e), file=self.fileDir, messagePrint=True)

    def cartInformation(self):
        log = Logger(f"Cart Information | {self.ProfileName}").log
        cartSuccessful = False
        while cartSuccessful == False:
            try:
                headers = {
                    'Host': 'selfridges.bookingbug.com',
                    'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="90", "Google Chrome";v="90"',
                    'App-Key': 'f0bc4f65f4fbfe7b4b3b7264b655f5eb',
                    'sec-ch-ua-mobile': '?0',
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
                    'Content-Type': 'application/json',
                    'Accept': 'application/hal+json,application/json',
                    'App-Id': 'f6b16c23',
                    'Auth-Token': self.authTokenHeader,
                    'Origin': 'https://bookings.selfridges.com',
                    'Referer': 'https://bookings.selfridges.com/',
                    'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
                }
                params = (
                    ('service_id', self.serviceID),
                )
                data = {
                    "entire_basket": True,
                    "items":[
                    {
                        "date": self.eventDate,
                        "time": self.eventSlotTimeNumber,
                        "event_id": self.eventID,
                        "price": 0,
                        "book":f"https://selfridges.bookingbug.com/api/v1/{self.storeID}/basket/add_item?service_id={self.serviceID}",
                        "id": self.checkoutID,
                        "duration": self.duration,
                        "settings": {
                            "resource":-1,
                            "person":-1,
                            "earliest_time": self.eventSlotDate
                        },
                        "child_client_ids":[
                        ],
                        "questions":self.questionForm,
                            "service_id": self.serviceID,
                            "resource_id":self.resourceID,
                            "person_id":self.personID,
                            "status":self.status,
                            "ref": int(self.referenceID)
                            }
                        ]
                }
                dataMetric = json.dumps(data, separators=(',', ':'))
                response = self.s.post(f'https://selfridges.bookingbug.com/api/v1/{self.storeID}/basket/add_item', headers=headers, params=params, data=dataMetric, timeout=45)
                log(response.request.body, color="yellow", file="Logs/Bookings", messagePrint=False)
                if response.status_code == 201 or response.status_code == '201':
                    jsonData = json.loads(response.text)
                    try:
                        if jsonData["_embedded"]["items"][0]["ref"] == int(self.referenceID) or jsonData["_embedded"]["items"][0]["ref"] == self.referenceID:
                            log(f"Succesfully updated form data at cart: {self.eventName} at {self.eventSlotDate}", color='green', file=self.fileDir, messagePrint=True)
                            responsedata = jsonData["_embedded"]["items"][0]
                            self.checkoutID = responsedata["id"]
                            log(f"Received updated checkoutID: {self.checkoutID}", color='yellow', file=self.fileDir, messagePrint=True)
                            cartSuccessful = True 

                    except IndexError or KeyError as e:
                        log(f"Unsucessfully updated form data at cart: {self.eventName} at {self.eventSlotDate} {self.eventSlotDate}", color='red', file=self.fileDir, messagePrint=True)
            

                elif response.status_code == 409 or response.status_code == '409':
                    jsonData = json.loads(response.text)
                    if jsonData["error"] == 'No Space Left':
                        log("Time slot unavailable, selecting new time slot...", color='magenta', file=self.fileDir, messagePrint=True)
                        self.getEventTimes()
                        self.cartTimeSlot()
                        continue

                    elif jsonData["error"] == 'Min advance time passed':
                        log("Can't update cart... Time slot too soon, selecting new time slot", color='magenta', file=self.fileDir, messagePrint=True)
                        self.dayIncrease = 2
                        self.getEventTimes()
                        self.cartTimeSlot()
                        continue

                    else:
                        log(f"Unknown 409 updating cart... | {response.status_code}\n{response.text}", color='red', file=self.fileDir, messagePrint=True)
                        self.getEventTimes()
                        self.cartTimeSlot()
                        continue
                
                elif 500 <= response.status_code <= 599:
                    log(f"Retrying adding slot information to cart: {response.status_code}", color='magenta', file=self.fileDir, messagePrint=True)
                    continue

                else:
                    log(f"UNKNOWN CART ERROR: {response.status_code}\n {response.text}", color='red', file=self.fileDir, messagePrint=True)
                    self.getEventTimes()
                    self.cartTimeSlot()
                    continue
            
            except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as e:
                        exc_type, exc_obj, exc_tb = sys.exc_info()
                        filename = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                        log("{}, {}, {}, {} - {}".format(exc_type, exc_tb.tb_lineno, exc_obj, filename, e), color="red", file=self.fileDir, messagePrint=False)
                        continue

            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                filename = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                log("{}, {}, {}, {} - {}".format(exc_type, exc_tb.tb_lineno, exc_obj, filename, e), file=self.fileDir, messagePrint=True)

    def checkout(self):
        log = Logger(f"Checkout | {self.ProfileName}").log
        checkedOut = False
        while checkedOut == False:
            try:
                headers = {
                    'Host': 'selfridges.bookingbug.com',
                    'sec-ch-ua': '" Not A;Brand";v="99", "Chromium";v="90", "Google Chrome";v="90"',
                    'App-Key': 'f0bc4f65f4fbfe7b4b3b7264b655f5eb',
                    'sec-ch-ua-mobile': '?0',
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36',
                    'Content-Type': 'application/json',
                    'Accept': 'application/hal+json,application/json',
                    'App-Id': 'f6b16c23',
                    'Auth-Token': self.authTokenHeader,
                    'Origin': 'https://bookings.selfridges.com',
                    'Referer': 'https://bookings.selfridges.com/',
                    'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
                }

                data = {
                "client":{
                    "consent":True,
                    "first_name":self.firstName,
                    "last_name":self.lastName,
                    "country":"United Kingdom",
                    "email":self.Email,
                    "id":self.profileID,
                    "notifications":{
                        
                    },
                    "mobile":self.mobileNoPrefix,
                    "mobile_prefix":self.mobilePrefix,
                    "questions":[
                        
                    ],
                    "extra_info":{
                        "locale":"en"
                    }
                },
                "is_admin":False,
                "items":[
                    {
                        "date": self.eventDate,
                        "time":self.eventSlotTimeNumber,
                        "event_id":self.eventID,
                        "price":0,
                        "book":f"https://selfridges.bookingbug.com/api/v1/{self.storeID}/basket/add_item?service_id={self.serviceID}",
                        "id":self.checkoutID,
                        "duration":self.duration,
                        "settings":{
                            "resource":-1,
                            "person":-1,
                            "earliest_time":self.eventSlotDate
                        },
                        "child_client_ids":[
                            
                        ],
                        "questions":self.questionForm,
                        "service_id":self.serviceID,
                        "resource_id":self.resourceID,
                        "person_id":self.personID,
                        "status":self.status,
                        "ref": int(self.referenceID)
                    }
                ]
                }
                dataMetric = json.dumps(data, separators=(',', ':'))
                response = self.s.post(f'https://selfridges.bookingbug.com/api/v1/{self.storeID}/basket/checkout', headers=headers, data=dataMetric, timeout=45)
                log(response.request.body, color="yellow", file="Logs/Bookings", messagePrint=False)
                if response.status_code == 201 or response.status_code == '201':
                    jsonData = json.loads(response.text)
                    try:
                        if jsonData["long_id"]:
                            if jsonData["client_name"] == f"{self.firstName} {self.lastName}":
                                log(f"Succesfully checked out! | {self.eventName} at {self.eventSlotDate}", color='green', file=self.fileDir, messagePrint=True)
                                self.formattedEventTime = jsonData["_embedded"]["bookings"][0]["describe"]
                                self.longCheckoutID = jsonData["long_id"]
                                checkedOut = True 
                    
                    except IndexError or KeyError as e:
                        log(f"Unsucessfully checked out...: {self.eventName} at {self.eventSlotDate} {self.eventSlotDate}\n{response.status_code}\n{response.text}", color='red', file=self.fileDir, messagePrint=True)

                elif response.status_code == 409 or response.status_code == '409':
                    jsonData = json.loads(response.text)
                    if jsonData["error"] == 'No Space Left':
                        log("Time slot unavailable, selecting new time slot...", color='magenta', file=self.fileDir, messagePrint=True)
                        self.getEventTimes()
                        self.cartTimeSlot()
                        self.cartInformation()
                        continue

                    elif jsonData["error"] == 'Min advance time passed':
                        log("Can't checkout... Time slot too soon, selecting new time slot", color='magenta', file=self.fileDir, messagePrint=True)
                        self.dayIncrease = 2
                        self.getEventTimes()
                        self.cartTimeSlot()
                        self.cartInformation()
                        continue

                    else:
                        log(f"Unknown 409 checkout error... | {response.status_code}\n{response.text}", color='red', file=self.fileDir, messagePrint=True)
                        self.getEventTimes()
                        self.cartTimeSlot()
                        self.cartInformation()
                        continue

                elif 500 <= response.status_code <= 599:
                    log(f"Retrying checkout: {response.status_code}", color='magenta', file=self.fileDir, messagePrint=True)
                    continue

                else:
                    log(f"UNKNOWN CHECKOUT ERROR | {response.status_code}\n{response.text}", color='red', file=self.fileDir, messagePrint=True)
                    self.getEventTimes()
                    self.cartTimeSlot()
                    self.cartInformation()
                    continue
            
            except (requests.exceptions.ConnectionError, requests.exceptions.ReadTimeout) as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                filename = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                log("{}, {}, {}, {} - {}".format(exc_type, exc_tb.tb_lineno, exc_obj, filename, e), color="red", file=self.fileDir, messagePrint=False)
                continue
                                   			
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                filename = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                log("{}, {}, {}, {} - {}".format(exc_type, exc_tb.tb_lineno, exc_obj, filename, e), file=self.fileDir, messagePrint=True)
    
    def webhookPosted(self):
        log = Logger(f"Webhook | {self.ProfileName}").log
        try:
            hook = self.webhook()
            embed = Webhook(hook, username="Selfridges Bookings Checkout", avatar_url=self.storeImage, color=3619134)
            embed.set_title(title=f"{self.storeName} | {self.eventName}", url=self.eventURL)
            #embed.add_field(name="Successful Booking!", value="", inline=False)


            embed.add_field(name="Store", value=f"{self.storeName}", inline=False)
            embed.add_field(name="Profile Name", value=f"{self.ProfileName}", inline=True)
            embed.add_field(name="Full Name", value=f"||{self.firstName} {self.lastName}||", inline=True)
            embed.add_field(name="Email", value=f"||{self.Email}||", inline=True)
            embed.add_field(name="Phone Number", value=f"||{self.Phone}||", inline=True)
            embed.add_field(name="TimeSlot", value=f"||{self.formattedEventTime}||", inline=True)
            embed.add_field(name="Duration", value=f"{self.duration} minutes", inline=True)
            embed.add_field(name="Checkout ID", value=f"{self.longCheckoutID}", inline=False)

            descList = []
            for i, data in enumerate(self.discordData, start=1):
                dataFormat = f"**{i}. {data['name']}**\n{data['answer']}"
                descList.append(dataFormat)
            descList = "\n".join(descList)
            embed.add_field(name="Questions", value=descList, inline=False)
            embed.set_thumbnail(self.storeImage)
            embed.set_footer(text='Selfridges Bookings Bot | agNotify', icon='https://cdn.discordapp.com/attachments/564554184410529802/756198795683037364/agnotify.png', ts=True)
            embed.post()

        
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            filename = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            log("{}, {}, {}, {} - {}".format(exc_type, exc_tb.tb_lineno, exc_obj, filename, e), file=self.fileDir, messagePrint=True)  
   
    def webhook(self):
        hook = hooks.pop(0)
        hooks.append(hook)
        return hook
    
    def saveData(self):
        log = Logger(self.ProfileName).log
        try:
            log(f"{self.storeName},{self.eventName}, {self.formattedEventTime}, {self.duration}, {self.checkoutID}, {self.referenceID} | {self.firstName},{self.lastName}, {self.Email}, {self.Phone}, {self.discordData}, {self.questionForm}", color='yellow', file="Logs/FinalSaved.txt", messagePrint=False)
        
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            filename = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            log("{}, {}, {}, {} - {}".format(exc_type, exc_tb.tb_lineno, exc_obj, filename, e), file=self.fileDir, messagePrint=True)

class SelfridgesMonitor:
    def __init__(self, proxy=None):
        self.proxy = proxy 
        self.fileDir = "Logs/Selfridges/Monitor"
        self.storeID = "37375"
        self.url = f"https://selfridges.bookingbug.com//api/v1/{str(self.storeID)}/services/?exclude_links[]=child_services"
    
    def createSession(self):
        self.s = requests.session()
        if self.proxy == None:
            pass
        else:
            self.s.proxies.update(self.proxy) 
    
    def getEvents(self):
        log = Logger("Monitor | getEvents").log
        gotEvent = False
        while gotEvent == False:
            try:
                headers = {
                    'Host': 'selfridges.bookingbug.com',
                    'accept': 'application/hal+json,application/json',
                    'app-id': 'f6b16c23',
                    'app-key': 'f0bc4f65f4fbfe7b4b3b7264b655f5eb',
                    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36 Edg/89.0.774.76',
                    'origin': 'https://bookings.selfridges.com',
                    'referer': 'https://bookings.selfridges.com/',
                    'accept-language': 'en-GB,en;q=0.9,en-US;q=0.8',
                }
                log("Submitting... get request!", color='yellow', file=self.fileDir, messagePrint=True)
                response = self.s.get(self.url, headers=headers)
                log("Submitted get request!", color='yellow', file=self.fileDir, messagePrint=True)
                if response.status_code == 200 or response.status_code == '200':
                    eventData = json.loads(response.text)
                    eventData = eventData["_embedded"]["services"]
                    eventList = []
                    for event in eventData:
                        #if 'wedding' in event["name"].lower() or 'tyds' in event["name"].lower():
                        if any(word in ['mystery','tyds','wedding', 'bag', 'appointment'] for word in event["name"].lower().split()):
                            eventList.append(event)
                            self.eventData = eventList
                            log(f'Filtered event found, adding to filtered list!: {event["name"]}', color='green', file=self.fileDir, messagePrint=True)
                            gotEvent = True

                        else:
                            log(f'Non filtered event found!: {event["name"]}', color='magenta', file=self.fileDir, messagePrint=True)

                elif response.status_code == 404 or response.status_code == '404':
                    eventData = json.loads(response.text)
                    if eventData["error"] == "Not Found":
                        log("No Events loaded...", file=self.fileDir, messagePrint=True)
                
                elif 500 <= response.status_code <= 599:
                    log(f"Retrying request statuse code: {response.status_code}", file=self.fileDir, messagePrint=True)
                    continue

                else:
                    log(f"Unknown response code: {response.status_code}\n{response.text}, {response.url}", file=self.fileDir, messagePrint=True)
            
            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                filename = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                log("{}, {}, {}, {} - {}".format(exc_type, exc_tb.tb_lineno, exc_obj, filename, e), file=self.fileDir, messagePrint=True)
                log(response.status_code, messagePrint=True)

    def getInfo(self):
        log = Logger("Monitor | Get Info").log
        gottenInfo = False
        while gottenInfo == False:
            try:
                #print(len(self.eventData))
                eventMetaDataList = []
                for index, event in enumerate(self.eventData):
                    eventName = event["name"]
                    serviceID = event["id"]
                    eventDescription = event["description"]
                    bookingTimeStep = event["booking_time_step"]
                    eventPrice = event["price"]
                    questionUrl = event["_links"]["questions"]["href"]

                    if eventPrice <= 0:
                        log("Event price is fine bro", color="green", file=self.fileDir, messagePrint=True)
                        headers = {
                            'Host': 'selfridges.bookingbug.com',
                            'accept': 'application/hal+json,application/json',
                            'app-id': 'f6b16c23',
                            'app-key': 'f0bc4f65f4fbfe7b4b3b7264b655f5eb',
                            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/89.0.4389.114 Safari/537.36 Edg/89.0.774.76',
                            'origin': 'https://bookings.selfridges.com',
                            'referer': 'https://bookings.selfridges.com/',
                            'accept-language': 'en-GB,en;q=0.9,en-US;q=0.8',
                        }
                        response = self.s.get(questionUrl, headers=headers, allow_redirects=False)
                        if 200 <= response.status_code <= 299:
                            jsonData = json.loads(response.text)
                            eventDataList = []
                            for index, data in enumerate(jsonData["questions"]):
                                optionList = []
                                questionName = data["name"]
                                questionID = data["id"]
                                detailType = data["detail_type"]
                                #eventDataList.append(questionName)
                                #eventDataList.append(questionID)
                                #eventDataList.append(detailType)
                                if detailType == "select":
                                    try:
                                        options = data["options"]
                                        for option in options:
                                            optionDict = {}
                                            optionName = option["name"]
                                            optionID = option["id"]
                                            optionDict[optionName] = optionID
                                            optionList.append(optionDict)
                                        #eventDataList.append(optionList)        
                                    except KeyError or TypeError:
                                        pass 
                                
                                questionsDict = {
                                        "index": index,
                                        "name": questionName,
                                        "id": questionID,
                                        "type": detailType,
                                        "options": optionList
                                }
                                eventDataList.append(questionsDict)
                            
                            eventMetaData = {
                                "Event Name": eventName,
                                "Store ID": self.storeID,
                                "Service ID": serviceID,
                                "Event Description": eventDescription,
                                "Booking Timestep": bookingTimeStep,
                                "Question URL": questionUrl,
                                "Question Data": eventDataList
                            }
                            #jsonData = json.loads(eventMetaData)
                            #jsonData = json.dumps(eventMetaData, indent=4)
                            #print(eventMetaData)
                            eventMetaDataList.append(eventMetaData)
                            gottenInfo = True

                        elif 400 <= response.status_code <= 599:
                            log(f"Retrying request status code: {response.status_code}", file=self.fileDir, messagePrint=True)
                            continue
                    else:
                        log("Event price is too expensive bro, gettoutta here...", color="red", file=self.fileDir, messagePrint=True)
                        pass
                    
                return eventMetaDataList

            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                filename = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                log("{}, {}, {}, {} - {}".format(exc_type, exc_tb.tb_lineno, exc_obj, filename, e), file=self.fileDir, messagePrint=True)
                           
def monitor():
    monitorInstance = SelfridgesMonitor()
    monitorInstance.createSession()
    monitorInstance.getEvents()
    eventData = monitorInstance.getInfo()
    return eventData

def bookings(eventData, profile):
    bookingsInstance = SelfridgesBookingCheckout(profile, data=eventData)
    bookingsInstance.timesIndex()
    bookingsInstance.setCheckoutInfo()
    bookingsInstance.createSession()
    bookingsInstance.getEventTimes()
    bookingsInstance.cartTimeSlot()
    bookingsInstance.updatePersonalData()
    bookingsInstance.cartInformation()
    bookingsInstance.checkout()
    bookingsInstance.webhookPosted()
    bookingsInstance.saveData()

def main():
    log = Logger("Main").log 
    try:
        with open("Profiles/agNotify.json", "r") as f:
            jsonProfiles = json.load(f)
            log(f"{len(jsonProfiles)} Selfridges Profile(s) loaded... ", color="blue", file="Logs/Monitor", messagePrint=True)
        
        eventsData = monitor()

        for profile in jsonProfiles:
            for eventData in eventsData:
                Thread(target=bookings, args=[eventData, profile]).start()

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        filename = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        log("{}, {}, {}, {} - {}".format(exc_type, exc_tb.tb_lineno, exc_obj, filename, e), file="Logs/Monitor", messagePrint=True)

if __name__ == "__main__":
    Path("Profiles/").mkdir(parents=True, exist_ok=True)
    Path("Logs/Selfridges/").mkdir(parents=True, exist_ok=True)

    hooks = [x.strip() for x in open("webhooks.txt").readlines()]
    main()
    pass