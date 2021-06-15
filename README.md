# SelfridgesBookingsBot

To start the monitor
Edit:
1. events.json

`python selfridges.py`

To start the bookings bot:
`python bookings.py`

Edit:
1. __init__() self.storeID for whatever store you want to montior
2. clients.json (where the information is sent to on hooks)


TO DO 
- [ ] Add a REQUIREMENTS.TXT FILE (not sure how to get all dependecies)
- [ ] Add better folder structure 
- [ ] Add database connector i.e. mongoDB instead of using json files, better for long term tracking 
- [ ] Add universal error handling 
