from pathlib import Path
import re
import sqlite3

import pandas as pd
import pypowerwall
from tenacity import retry, wait_fixed, stop_after_attempt

import mysecrets


@retry(wait=wait_fixed(2), stop=stop_after_attempt(8))
def get_tesla_data():
    pw = pypowerwall.Powerwall(
        host=mysecrets.HOST,
        password=mysecrets.PASSWORD,
        email=mysecrets.EMAIL,
        timezone="America/New_York",
    )

    agg = pw.poll("/api/meters/aggregates", jsonformat=True)
    soe = pw.poll("/api/system_status/soe", jsonformat=True)
    grid = pw.poll("/api/system_status/grid_status", jsonformat=True)
    sys = pw.poll("/api/system_status", jsonformat=True)

    tdata = dict(
        lastcomm=agg["load"]["last_communication_time"],
        sitepower=float(agg["site"]["instant_power"]),
        loadpower=float(agg["load"]["instant_power"]),
        solarpower=float(agg["solar"]["instant_power"]),
        batterypower=float(agg["battery"]["instant_power"]),
        battlevel=float(soe["percentage"]),
        battcap=float(sys["nominal_full_pack_energy"]),
        gridstat=grid["grid_status"],
    )

    # Strip milliseconds from date
    tdata["lastcomm"] = re.sub(r"\.\d+-", "-", tdata["lastcomm"])

    return tdata


def add_api_rec_to_database(tdata):
    """Add the latest data record captured through
    the Tesla API to the sqlite database.
    """
    DBFILE = "../data/energy.sqlite"

    COLUMNS = "DateTime,Grid_kW,Home_kW,Solar_kW,Powerwall_kW,BattLevel,BattCapacitykWh,GridStatus".split(
        ","
    )
    ORWELLSHARE = 0.26  # Our share of Orwell panel output
    ORWELLSOLARMAX = 14.22 * ORWELLSHARE  # Maximum observed output
    HOMESOLARMAX = 5.3  # Maximum observed output

    fields = list(tdata.values())
    df = pd.DataFrame([fields], columns=COLUMNS)

    # Convert numbers to kilowatts
    df[["Grid_kW", "Home_kW", "Solar_kW", "Powerwall_kW", "BattCapacitykWh"]] /= 1000

    df["DateTime"] = pd.to_datetime(df["DateTime"], utc=True)
    df = df.set_index(["DateTime"])

    # Open the database and read the last timestamp.
    con = sqlite3.connect(DBFILE)
    cursor = con.cursor()
    cursor.execute("SELECT DateTime FROM energy_data ORDER BY DateTime DESC LIMIT 1")
    lastdate = pd.to_datetime(cursor.fetchone()[0], utc=True)

    # Get the last reading from the Orwell panels - this acquired via:
    #   ~/Sunpower/sunpower_hass/venv/bin/python -msunpower -c ~/Sunpower/sunpower_hass/sunpower.cfg
    # which is run every minute via cron.
    try:
        orwellout = Path("/sunpower/sunpower").read_text()
        orwellout = float(orwellout) * ORWELLSHARE
    except (FileNotFoundError, ValueError, TypeError) as e:
        orwellout = 0.00009

    df["Orwell_kW"] = orwellout

    # Get time delta
    td = df.index[0] - lastdate.to_pydatetime()

    # Add calculated fields
    df["delta_hours"] = td.total_seconds() / 3600
    df["Home_kWh"] = df["Home_kW"] * df["delta_hours"]
    df["Solar_kWh"] = df["Solar_kW"] * df["delta_hours"]
    df["Powerwall_kWh"] = df["Powerwall_kW"] * df["delta_hours"]
    df["Grid_kWh"] = df["Grid_kW"] * df["delta_hours"]
    df["Orwell_kWh"] = df["Orwell_kW"] * df["delta_hours"]

    # Add to the database
    df.to_sql("energy_data", con, if_exists="append")


tdata = get_tesla_data()
add_api_rec_to_database(tdata)
