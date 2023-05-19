# Import the dependencies.
from matplotlib import style
style.use('fivethirtyeight')
import matplotlib.pyplot as plt
import pandas as pd
import datetime as dt
import numpy as np
from dateutil.relativedelta import relativedelta
from flask import Flask, jsonify
import sqlalchemy
from  sqlalchemy.ext.automap import automap_base
from  sqlalchemy.orm import Session
from  sqlalchemy import create_engine, func
import os as os
print(os.getcwd())
#################################################
# Database Setup
#################################################
# reflect an existing database into a new model
engine = create_engine("sqlite:///SurfsUp/Resources/hawaii.sqlite")
Base = automap_base()
# reflect the tables
Base.prepare(engine, reflect=True)
# Save references to each table
measurement = Base.classes.measurement
station = Base.classes.station
# Create our session (link) from Python to the DB
session = Session(engine)

# Some common code used in Flask Routes
################################################################################################
# Design a query to retrieve the last 12 months of precipitation data and plot the results. 
# Starting from the most recent data point in the database.
most_recent_date=session.query(measurement.date).order_by(measurement.date.desc()).first()
most_recent_date=most_recent_date[0]
# Calculate the date one year from the last date in data set.
twelve_mo_before= dt.datetime.strptime(most_recent_date, '%Y-%m-%d') - relativedelta(months=12)
twelve_mo_before=dt.datetime.strftime(twelve_mo_before, '%Y-%m-%d')
twelve_mo_before
#find most active station
station_counts=[]
stations_list=[]
for row in session.query(station.station):
    stations_list.append(row[0])
for stat in stations_list:
    station_counts.append((stat,len(session.query(measurement.station).filter_by(station=stat).all())))
station_counts
x=0
for row in station_counts:
    if row[1]>x:
        x=row[1]
        top_station=row[0]

#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Flask Routes
#################################################
@app.route("/")
def welcome():
    return (
        f"Welcome to Hawaii Weather API!<br/>"
        f"Available Routes:<br/>"
        f"Precipitation data for last year:<br/>"
        f"/api/v1.0/precipitation<br/>"
        f"List of available stations:<br/>"
        f"/api/v1.0/stations<br/>"
        f"Temperature data for last year:<br/>"
        f"/api/v1.0/tobs<br/>"
        f"For summary data from start date to latest observation:<br/>"
        f"/api/v1.0/YYYY-MM-DD<br/>"
        f"For summary data between two dates (start, end):<br/>"
        f"/api/v1.0/YYYY-MM-DD/YYYY-MM-DD"
        )

@app.route("/api/v1.0/precipitation")
def precipitation():
    # Perform a query to retrieve the date and precipitation scores
    recent12mo=engine.execute(f'SELECT date, prcp FROM measurement WHERE measurement.date > "{twelve_mo_before}" AND measurement.date <= "{most_recent_date}"')
    # Save the query results as a Pandas DataFrame. Explicitly set the column names
    df=pd.DataFrame({'Date':[],'Precipitation':[]})
    for entry in recent12mo:
        print(entry)
        df=df.append({'Date':entry[0],'Precipitation':entry[1]}, ignore_index=True)
    # Sort the dataframe by date
    df=df.sort_values('Date', ascending=True)
    df=df.reset_index(0,len(df))
    # Convert dataframe to dictionary
    df_dic={}
    for row in range(0,len(df)):
        df_dic[df.loc[row]['Date']]=df.loc[row]['Precipitation']

    return jsonify(df_dic)

@app.route("/api/v1.0/stations")
def stations():
    stations_list=[]
    for row in session.query(station.name, station.station):
        stations_list.append({row[1]:row[0]})

    return jsonify(stations_list)

@app.route("/api/v1.0/tobs")
def last12mo_temp():
    #query temperature and dates
    temp_last12mo_query=session.query(measurement.date,measurement.tobs).filter(measurement.station==top_station).filter(measurement.date > twelve_mo_before).all()
    temp_last12mo=[]
    for t in temp_last12mo_query:
        temp_last12mo.append({t[0]:t[1]})

    return jsonify(temp_last12mo)

@app.route("/api/v1.0/<start>")
def start_lookup(start):
    
    start=dt.datetime.strptime(start, '%Y-%m-%d')
    temps_query=session.query(measurement.tobs).filter(measurement.station==top_station).filter(measurement.date>=start).all()
    temps=[]
    for t in temps_query:
        temps.append(t[0])
    min_max_ave_temp={'start_date':start, 'end date':most_recent_date, 'min temp':min(temps), 'max temp':max(temps), 'average temp':sum(temps)/len(temps)}
    
    return jsonify(min_max_ave_temp)

@app.route("/api/v1.0/<start2>/<end>")
def start_end_lookup(start2,end):
    start=dt.datetime.strptime(start2, '%Y-%m-%d')
    end=dt.datetime.strptime(end, '%Y-%m-%d')
    temps_query=session.query(measurement.tobs).filter(measurement.station==top_station).filter(measurement.date>=start2).filter(measurement.date<=end).all()
    temps=[]
    for t in temps_query:
        temps.append(t[0])
    min_max_ave_temp={'start_date':start2, 'end date':end, 'min temp':min(temps), 'max temp':max(temps), 'average temp':sum(temps)/len(temps)}
    
    return jsonify(min_max_ave_temp)








if __name__ == "__main__":
    app.run(debug=True)