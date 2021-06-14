import requests, json, time, os, sys
from Classes.discord_hooks import Webhook
from pathlib import Path 
from Classes.logger import Logger
from threading import Thread

class SelfridgesBookingMonitor:
    def __init__(self, eventsJson, index):
        self.jsonIndex = index
        self.s = requests.session()
        self.storeName = eventsJson["storeName"]
        self.storeID = eventsJson["storeID"]  # get from eventsJson
        self.storeImage = eventsJson["storeImage"]
        self.url = f"https://selfridges.bookingbug.com//api/v1/{str(self.storeID)}/services/?exclude_links[]=child_services"
        self.eventURL = f"https://bookings.selfridges.com/selfridges-body-denim/new_booking.html?companyId={self.storeID}#/service_list"
        self.fileDir = "Logs/Selfridges/Monitoring/monitor.log"

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
                        # if 'wedding' in event["name"].lower() or 'tyds' in event["name"].lower():
                        if any(word in ['mystery', 'tyds', 'wedding', 'bag', 'appointment', 'meeting'] for word in event["name"].lower().split()):
                            eventList.append(event)
                            self.eventData = eventList
                            log(f'Filtered event found, added to filtered list: {event["name"]}', color='blue', file=self.fileDir, messagePrint=True)
                            gotEvent = True 


                        else:
                            log(f'Non filtered event found!: {event["name"]}', color='magenta', file=self.fileDir, messagePrint=True)
                    return True 

                elif 400 <= response.status_code <= 499:
                    if response.status_code == 404 or response.status_code == '404':
                            eventData = json.loads(response.text)
                            if eventData["error"] == "Not Found":
                                #log("No Events loaded...", file=self.fileDir, messagePrint=True)
                                with open("events.json", "r+") as f:
                                    jsonData = json.load(f)
                                    i = jsonData[self.jsonIndex]
                                    if i["currentActiveEvents"] == []:
                                        log("No Events loaded...", file=self.fileDir, messagePrint=True)
                                        gotEvent = True 
                                        pass 
                                    else:
                                        for event in i["currentActiveEvents"]:
                                            if event in i["oldEvents"]:
                                                i["currentActiveEvents"].remove(event)
                                                log("No events found... emptied last current event list", file=self.fileDir, messagePrint=True)
                                                gotEvent = True           

                                            elif event not in i["oldEvents"]:
                                                i["oldEvents"].append(event)
                                                i["currentActiveEvents"].remove(event)
                                                log("No events found... moved last current event to old events...", file=self.fileDir, messagePrint=True)
                                                gotEvent = True 
                                    
                                    with open("events.json", "w+") as f:
                                        log("Editing events.json...")
                                        json.dump(jsonData, f, ensure_ascii=False, indent=4)
                                        
                    else:
                        log(f"Unknown 400-499 error getting event: {response.status_code} - {response.text}", file=self.fileDir, messagePrint=True)

                elif 500 <= response.status_code <= 599:
                    log(f"Retrying request statuse code: {response.status_code}", file=self.fileDir, messagePrint=True)
                    continue

                else:
                    log(f"Unknown response code: {response.status_code}\n{response.text}, {response.url}", file=self.fileDir, messagePrint=True)

            except Exception as e:
                exc_type, exc_obj, exc_tb = sys.exc_info()
                filename = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
                log("{}, {}, {}, {} - {}".format(exc_type, exc_tb.tb_lineno, exc_obj, filename, e), file=self.fileDir, messagePrint=True)

    def getEventMicroData(self, event):
        log = Logger("Event Microdata").log
        try:
            embeddedEvents = event
            self.eventName = embeddedEvents["name"]
            eventID = embeddedEvents["id"]
            try:
                eventDescription = embeddedEvents["description"]
            except KeyError:
                eventDescription = None
            try:
                eventPrice = embeddedEvents["price"]
            except KeyError:
                eventPrice = None
            eventPrices = [str(x)for x in embeddedEvents["prices"]]
            try:
                bookingTimeStep = embeddedEvents["booking_time_step"]
            except KeyError:
                bookingTimeStep = None

            jsonObject = {
                "eventName": self.eventName,
                "eventID": eventID,
                "eventDiscription": eventDescription,
                "bookingTimeStep": bookingTimeStep,
                "eventPrices": eventPrices,
                "eventPrice": eventPrice,
            }
            return jsonObject

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            filename = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            log("{}, {}, {}, {} - {}".format(exc_type, exc_tb.tb_lineno,
                exc_obj, filename, e), file=fileDir, messagePrint=True)

    def findEvents(self):
        log = Logger("Sorting Events").log
        try:
            with open("events.json", "r+") as f:
                jsonData = json.load(f)
                i = jsonData[self.jsonIndex]

                for event in self.eventData:
                    microDataJson = self.getEventMicroData(event)
                    if i["storeName"] == self.storeName:

                        if microDataJson in i["currentActiveEvents"]:
                            log("Event found is current and active, re-searching...: {}".format(self.eventName), color='blue', file=fileDir, messagePrint=True)
                            self.eventType = "Active"

                        elif microDataJson not in i["currentActiveEvents"]:
                            if microDataJson in i["oldEvents"]:
                                log("Event found is old and not active, ping restock: {}".format(self.eventName), color='green', file=fileDir, messagePrint=True)
                                self.eventType = "Restock"
                                self.webhookPrepare(microDataJson)
                                i["currentActiveEvents"].append(microDataJson)

                            elif microDataJson not in i["oldEvents"]:
                                log("Event found is completely new, ping new event found!: {}".format(self.eventName), color='green', file=fileDir, messagePrint=True)
                                self.eventType = "New"
                                self.webhookPrepare(microDataJson)
                                i["currentActiveEvents"].append(microDataJson)
                                i["oldEvents"].append(microDataJson)
            
            with open("events.json", "w+") as f:
                json.dump(jsonData, f, ensure_ascii=False, indent=4)

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            filename = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            log("{}, {}, {}, {} - {}".format(exc_type, exc_tb.tb_lineno, exc_obj, filename, e), file=fileDir, messagePrint=True)

    def webhookPrepare(self, microDataJson):
        log = Logger("Webhook").log
        try:
            with open("clients.json", "r+") as f:
                jsonData = json.load(f)
            
            for hookData in jsonData:
                Thread(target=self.webhookPost, args=[hookData, microDataJson]).start()

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            filename = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            log("{}, {}, {}, {} - {}".format(exc_type, exc_tb.tb_lineno, exc_obj, filename, e), file=self.fileDir, messagePrint=True)
   
    def webhookPost(self, hookData, microDataJson):
        try:
            log = Logger("Webhook").log
            Client = hookData["Client"]
            HookName = hookData["Hook Name"]
            HookFooter = hookData["Hook Footer"]
            HookColour = hookData["Hook Colour"]
            HookIcon = hookData["Hook Icon URL"]
            Hooks = hookData["Webhooks"]
            hook = self.webhook(Hooks)
            CustomMessage = hookData["Custom Message"]

            embed = Webhook(hook, username=HookName, avatar_url=self.storeImage, content=CustomMessage, color=HookColour)

            if self.eventType == "New": embed.set_title(title="{} Bookings - NEW EVENT FOUND".format(self.storeName), url=self.eventURL)
            elif self.eventType == "Restock": embed.set_title(title="{} Bookings".format(self.storeName), url=self.eventURL)

            embed.add_field(name="Event Name",value=microDataJson["eventName"], inline=True)
            embed.add_field(name="Duration", value=str(microDataJson["bookingTimeStep"]) + " minutes", inline=True)
            price = microDataJson["eventPrice"]
            
            if price == 0 or price == '0':
                price = "Complimentary"
            elif price == None:
                price = microDataJson["eventPrices"][0]

            embed.add_field(name="Price", value=price, inline=True)
            embed.set_thumbnail(self.storeImage)
            embed.set_footer(text=HookFooter, icon=HookIcon, ts=True)
            embed.post()
            return True

        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            filename = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            log("{}, {}, {}, {} - {}".format(exc_type, exc_tb.tb_lineno, exc_obj, filename, e), file=fileDir, messagePrint=True)

    def webhook(self, Hooks):
        hook = Hooks.pop(0)
        Hooks.append(hook)
        return hook

def openEventsJson():
    log = Logger("events.json").log
    try:
        with open("events.json", "r+") as f:
            jsonData = json.load(f)
            return jsonData

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        filename = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        log("Exception | {}, {}, {}, {}".format(exc_type, exc_tb.tb_lineno, e, filename), file=fileDir, messagePrint=True)

def main():
    log = Logger("Main Function").log
    try:
        while True:
            eventsJsons = openEventsJson()
            for index, eventsJson in enumerate(eventsJsons):
                instance = SelfridgesBookingMonitor(eventsJson, index)
                response = instance.getEvents()
                if response == True:
                    instance.findEvents()
                else:
                    pass

    except Exception as e:
        exc_type, exc_obj, exc_tb = sys.exc_info()
        filename = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        log("Exception | {}, {}, {}, {}".format(exc_type, exc_tb.tb_lineno, e, filename), file=fileDir, messagePrint=True)

if __name__ == "__main__":
    pathLog = "Logs/Selfridges/Monitoring"
    Path(pathLog).mkdir(parents=True, exist_ok=True)
    fileDir = pathLog + "monitor.log"
    main()
