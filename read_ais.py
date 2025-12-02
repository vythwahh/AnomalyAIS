import pandas as pd
from datetime import timedelta
MIN_GAP = timedelta(seconds=1)     
CONFIRM_WINDOW = timedelta(seconds=3)
CONFIRM_COUNT = 2

CRITICAL_10 = timedelta(minutes=10)
REPEAT_10 = timedelta(minutes=10)
MONITOR_WINDOW = timedelta(hours=1)      

 
df = pd.read_csv(r"/Users/vythu/Documents/AIS Project/test_ais_logic.csv")
df['timestamp'] = pd.to_datetime(df['timestamp'])
df = df.sort_values(["vessel_id", "timestamp"])

 
state = {}                
last_seen = {}            
lost_start = {}          
monitor_start = {}       
last_critical = {}        
confirm_buffer = {}      


 
for _, row in df.iterrows():
    ship = row["vessel_id"]
    ts   = row["timestamp"]

    # init ship
    if ship not in state:
        state[ship] = "OK"
        last_seen[ship] = ts
        confirm_buffer[ship] = []
        monitor_start[ship] = None
        lost_start[ship] = None
        last_critical[ship] = None
        continue

    # compute gap
    gap = ts - last_seen[ship]

   
    if gap > MIN_GAP:

      
        print(f"[ALERT] {ship} lost AIS at {ts} (gap {gap})")

    
        state[ship] = "LOST"
        lost_start[ship] = ts

 
        monitor_start[ship] = ts
        last_critical[ship] = ts       
        confirm_buffer[ship] = []

        last_seen[ship] = ts
        continue

 
    confirm_buffer[ship].append(ts)
    confirm_buffer[ship] = [t for t in confirm_buffer[ship] if ts - t <= CONFIRM_WINDOW]

  
    if len(confirm_buffer[ship]) >= CONFIRM_COUNT:

        if state[ship] == "LOST":
            print(f"[INFO] {ship} regained AIS at {ts}")
            state[ship] = "MONITORING"      
        confirm_buffer[ship] = []
 
    if state[ship] == "LOST":

        
        if ts - lost_start[ship] >= CRITICAL_10 and last_critical[ship] == lost_start[ship]:
            print(f"[CRITICAL] {ship} offline > 10 minutes at {ts}")
            last_critical[ship] = ts

       
        elif ts - last_critical[ship] >= REPEAT_10:
            print(f"[CRITICAL REPEAT] {ship} still offline at {ts}")
            last_critical[ship] = ts

 
    if state[ship] == "MONITORING":
        if ts - monitor_start[ship] > MONITOR_WINDOW:
 
            state[ship] = "OK"
            monitor_start[ship] = None
            lost_start[ship] = None
            last_critical[ship] = None

    last_seen[ship] = ts
 
 
