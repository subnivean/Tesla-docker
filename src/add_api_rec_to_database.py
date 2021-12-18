#!/usr/bin/env python
"""Add the latest data record captured through
the Tesla API to the sqlite database. Piped to
from inside `get_tesla_gateway_meter_data.sh`.
"""
from pathlib import Path
import sqlite3
import sys

DBFILE = '../data/energy.sqlite'
import pandas as pd

# Data record is being piped in from bash
# script `get_tesla_gateway_meter_data.sh`
# apirec = '"2021-12-08T21:20:33-04:00",  9999.26,  1256.49,     4.19,   -10.00,   100.00, 11193.00, "SystemGridConnected"'
#apirec = " ".join(sys.argv[1:])
apirec = sys.stdin.read()

COLUMNS = "DateTime,Grid_kW,Home_kW,Solar_kW,Powerwall_kW,BattLevel,BattCapacitykWh,GridStatus".split(',')
ORWELLSHARE = 0.26  # Our share of Orwell panel output
ORWELLSOLARMAX = 14.22 * ORWELLSHARE  # Maximum observed output
HOMESOLARMAX = 5.3  # Maximum observed output

fields = [f.strip().strip('"') for f in apirec.split(",")]
fields[1:-1] = map(float, fields[1:-1])
df = pd.DataFrame([fields], columns=COLUMNS)
# Convert numbers to kilowatts
df[['Grid_kW', 'Home_kW', 'Solar_kW', 'Powerwall_kW', 'BattCapacitykWh']] /= 1000

df['DateTime'] = pd.to_datetime(df['DateTime'], utc=True)
df = df.set_index(['DateTime'])

# Open the database and read the last timestamp.
con = sqlite3.connect(DBFILE)
cursor = con.cursor()
cursor.execute("SELECT DateTime FROM energy_data ORDER BY DateTime DESC LIMIT 1")
lastdate = pd.to_datetime(cursor.fetchone()[0], utc=True)

# Get the last reading from the Orwell panels - this acquired via:
#   ~/Sunpower/sunpower_hass/venv/bin/python -msunpower -c ~/Sunpower/sunpower_hass/sunpower.cfg
# which is run every minute via cron.
try:
    orwellout = Path("/tmp/sunpower").read_text()
    orwellout = float(orwellout) * ORWELLSHARE
except (FileNotFoundError, ValueError, TypeError) as e:
    orwellout = 0.0

df['Orwell_kW'] = orwellout

# Get time delta
td = df.index[0] - lastdate.to_pydatetime()

# Add calculated fields
df['delta_hours'] = td.total_seconds() / 3600
df['Home_kWh'] = df['Home_kW'] * df['delta_hours']
df['Solar_kWh'] = df['Solar_kW'] * df['delta_hours']
df['Powerwall_kWh'] = df['Powerwall_kW'] * df['delta_hours']
df['Grid_kWh'] = df['Grid_kW'] * df['delta_hours']
df['Orwell_kWh'] = df['Orwell_kW'] * df['delta_hours']

# Add to the database
df.to_sql('energy_data', con, if_exists='append')

# homepctofmax = df['Solar_kW'][0] / HOMESOLARMAX * 100
# orwellpctofmax = orwellout / ORWELLSOLARMAX * 100
# print(f"orwellout: {orwellout * 1000:.2f} "
        # f"({orwellpctofmax / homepctofmax * 100:.1f}%)")
