import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

# ============================
# CONFIG
# ============================
NUM_SHIPS = 25
HOURS = 24
POINT_INTERVAL = 1   # seconds
TOTAL_SECONDS = HOURS * 3600
OUTPUT = "big_ais_24h_25ships.csv"

# Seychelles – Madagascar – Comoros region
LAT_MIN, LAT_MAX = -20.0, -4.0
LON_MIN, LON_MAX =  40.0, 65.0

# Suspicious behaviors
P_SUSTAINED_LOSS = 0.05     # 5% tàu tắt liên tục
P_INTERMITTENT = 0.20       # 20% tàu tắt bật bất thường

# Loss behavior parameters
SUSTAINED_LOSS_MIN = 20 * 60   # 20 phút
SUSTAINED_LOSS_MAX = 40 * 60   # 40 phút
INTERMITTENT_MIN = 2           # 2 giây
INTERMITTENT_MAX = 30          # 30 giây

# ============================
# RANDOM SHIP BEHAVIOR ASSIGNMENT
# ============================
ships = [f"SHIP{str(i+1).zfill(3)}" for i in range(NUM_SHIPS)]
ship_behavior = {}

for s in ships:
    r = random.random()
    if r < P_SUSTAINED_LOSS:
        ship_behavior[s] = "sustained_loss"
    elif r < P_SUSTAINED_LOSS + P_INTERMITTENT:
        ship_behavior[s] = "intermittent"
    else:
        ship_behavior[s] = "normal"

# ============================
# GENERATE POINTS
# ============================
rows = []
start_time = datetime(2025, 12, 1, 0, 0, 0)

def jitter(val, scale=0.01):
    return val + np.random.uniform(-scale, scale)

for ship in ships:
    lat = np.random.uniform(LAT_MIN, LAT_MAX)
    lon = np.random.uniform(LON_MIN, LON_MAX)

    t = start_time
    lost_until = None  # time until which AIS is off

    for second in range(TOTAL_SECONDS):

        # Nếu tàu trong sustained-loss mode
        if ship_behavior[ship] == "sustained_loss":
            # Nếu chưa bắt đầu mất, random kích hoạt
            if lost_until is None and random.random() < 0.0005:
                duration = random.randint(SUSTAINED_LOSS_MIN, SUSTAINED_LOSS_MAX)
                lost_until = t + timedelta(seconds=duration)

            # Nếu đang mất AIS → skip ghi điểm
            if lost_until and t < lost_until:
                t += timedelta(seconds=1)
                continue
            # Nếu đã qua thời gian mất → reset
            if lost_until and t >= lost_until:
                lost_until = None

        # Nếu tàu intermittent
        if ship_behavior[ship] == "intermittent":
            # Cơ hội nhỏ để mất bất thường
            if random.random() < 0.002:
                duration = random.randint(INTERMITTENT_MIN, INTERMITTENT_MAX)
                lost_until = t + timedelta(seconds=duration)

            if lost_until and t < lost_until:
                t += timedelta(seconds=1)
                continue
            if lost_until and t >= lost_until:
                lost_until = None

        # Normal drift
        lat = jitter(lat, 0.005)
        lon = jitter(lon, 0.005)

        rows.append([t, ship, lat, lon])
        t += timedelta(seconds=1)

# ============================
# SAVE CSV
# ============================
df = pd.DataFrame(rows, columns=["timestamp", "vessel_id", "lat", "lon"])
df.to_csv(OUTPUT, index=False)

print(f"\nGenerated dataset: {OUTPUT}")
print(df.head())
print("\nTotal rows:", len(df))
df = pd.read_csv("big_ais_24h_25ships.csv")
