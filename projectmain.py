import matplotlib.pyplot as plt
import pandas as pd
from _datetime import datetime
from pandas.plotting import register_matplotlib_converters
from sortedcontainers import SortedDict, SortedSet, SortedList
import math
import calendar
from sklearn import cluster
from collections import Counter, defaultdict
import numpy as np
from dateutil import parser

pd.set_option('display.max_columns', 5)
dfQ1 = pd.read_csv("HealthyRideRentals2019-Q1.csv")
dfQ2 = pd.read_csv("HealthyRideRentals2019-Q2.csv")
dfQ3 = pd.read_csv("HealthyRideRentals2019-Q3.csv")
filter_month = 4
filter_stationID = 1046
# {StationId :{day:[from,to,balancing]} }
station_records = dict(dict(dict()))
station_ids = []
# keeps the time info to calculate rebalancing
# {bikeID:{date_time:[from,to,starttime]} }
dates_time = dict(SortedDict([]))
# use a sorted date list to use as column names later
date_as_column = SortedList()


# print(dfQ2)
# Check if a bike was rebalanced
quaters = [dfQ1, dfQ2, dfQ3]
for df in quaters:
    for index, row in df.iterrows():
        from_sta_id = row['From station id']
        to_sta_id = row['To station id']
        bike_id = row['Bikeid']
        #start_date = datetime.strptime(row['Starttime'], '%m/%d/%y %H:%M')
        #stop_date = datetime.strptime(row['Stoptime'], '%m/%d/%y %H:%M')
        start_date = parser.parse(row['Starttime'])
        stop_date = parser.parse(row['Stoptime'])
        start_day = start_date.date()
        stop_day = stop_date.date()
        # store the start time of each bike in sorted order
        if bike_id in dates_time:
            new_list = [from_sta_id, to_sta_id,start_day]
            dates_time[bike_id].update({stop_date:new_list})

        else:
            dates_time[bike_id] = {stop_date: [from_sta_id, to_sta_id,start_day]}
        if start_day not in date_as_column:
            date_as_column.add(start_day)
        if stop_day not in date_as_column:
            date_as_column.add(stop_day)
        # print(day,date)
        # check if the from station_id is valid
        # print(type(from_sta_id),from_sta_id)
        if not math.isnan(from_sta_id):
            if from_sta_id in station_records:
                if start_day in station_records[from_sta_id]:
                    station_records[from_sta_id][start_day]['fromCNT'] += 1
                else:
                    new_day = {'fromCNT': 1, 'toCNT': 0, 'rebalCNT': 0}
                    station_records[from_sta_id][start_day] = new_day
            else:
                station_records[from_sta_id] = {start_day: {'fromCNT': 1, 'toCNT': 0, 'rebalCNT': 0}}
        # check if the to station_id is valid

        if not math.isnan(to_sta_id):
            if to_sta_id in station_records:
                if stop_day in station_records[to_sta_id]:
                    station_records[to_sta_id][stop_day]['toCNT'] += 1
                else:
                    new_day = {'fromCNT': 0, 'toCNT': 1, 'rebalCNT': 0}
                    station_records[to_sta_id][stop_day] = new_day
            else:
                station_records[to_sta_id] = {stop_day: {'fromCNT': 0, 'toCNT': 1, 'rebalCNT': 0}}
sorted_dates_time = dict(dict([]))
for id,times in dates_time.items():
    sorted_dates_time[id] = {}
    sorted_times = sorted(times.keys())
    new_dict = dict()
    for k in sorted_times:
        new_dict[k] = dates_time[id][k]
    sorted_dates_time[id] = new_dict
#for d,v in sorted_dates_time[70392].items():
#    if d.month == 4:
#        print(d,v)
for key, value in sorted_dates_time.items():
    time_list_each_bike = list(value.keys())
    list_length = len(time_list_each_bike)
    for i in range(list_length - 1, 1, -1):
        # start from the end, if last stop id != current from id, rebalanced
        last_stop_id = value[time_list_each_bike[i - 1]][1]
        this_from_id = value[time_list_each_bike[i]][0]
        date = value[time_list_each_bike[i]][2]
        #date = time_list_each_bike[i].date()
        # Go increment this from id's rebalanced count at that day
        if last_stop_id != this_from_id and not math.isnan(this_from_id) and not math.isnan(last_stop_id) :
            #print(this_from_id,last_stop_id)
            station_records[this_from_id][date]['rebalCNT'] += 1
#print(dates_time[70392].keys())
# turn all data into a dataframe
df1 = pd.DataFrame({'station_id': list(station_records.keys())})
for d in reversed(date_as_column):
    column_data = []
    for value in station_records.values():
        if d in value:
            column_data.append(value[d])
        else:
            column_data.append(None)
    df1[d] = column_data
#print(df1.head(20))
# aggragate by month now

df2 = pd.DataFrame({'station_id': list(station_records.keys())})
station_records_by_month = dict(dict(dict()))
for key, value in station_records.items():
    station_records_by_month[key] = {}
    for days in value:
        from_count = value[days]['fromCNT']
        to_count = value[days]['toCNT']
        rebal_count = value[days]['rebalCNT']
        # testd = station_records[filter_stationID][datetime.strptime('5/16/19 00:00', '%m/%d/%y %H:%M').date()]
        if days.month in station_records_by_month[key]:
            station_records_by_month[key][days.month]['fromCNT'] += from_count
            station_records_by_month[key][days.month]['toCNT'] += to_count
            station_records_by_month[key][days.month]['rebalCNT'] += rebal_count
        else:
            station_records_by_month[key][days.month] = {'fromCNT': from_count, 'toCNT': to_count,
                                                         'rebalCNT': rebal_count}

# for item in station_records[filter_stationID]:
#    if item.month == 5:
#        print(item,station_records[filter_stationID][item])

# turn all data into a dataframe
for d in reversed(date_as_column):
    month = d.month
    if month in df2:
        continue
    column_data = []
    for value in station_records_by_month.values():
        if month in value:
            column_data.append(value[month])
        else:
            column_data.append(None)
    df2[month] = column_data
# j = 0
# for k,v in station_records_by_month.items():
#    print(k,v)
#    j += 1
#    if j == 20:
#        break
# i = 0
# for key,value in station_records.items():
#    print(key,value)
#    i += 1
#    if i == 20:
#        break
# check_rebalance(row['bike id'],row['from station id']):
# print(station_records_by_month[1000][4])
# Task 2.1
plt.rcParams.update({'font.size': 10})
from_count_list = list()
station_ranking = ['0'] * 25
for sta_id, month_reports in station_records_by_month.items():
    if filter_month in month_reports:
        from_count_list.append(month_reports[filter_month]['fromCNT'])
from_count_list.sort(reverse=True)

for id, data in station_records_by_month.items():
    if filter_month in data:
        fromCNT = data[filter_month]['fromCNT']
        index = from_count_list.index(fromCNT)
        if index < 25:
            station_ranking[index] = str(id)
plt.figure(figsize=(15, 10))
plt.bar(station_ranking, from_count_list[0:25])
plt.title('Most popular stations for %s' % calendar.month_name[filter_month])
plt.xlabel('stationID')
plt.ylabel('FromCNT')
plt.show()

# Task 2.2
# get all the days of that month
days_list = []
fromCNT_for_each_day = []
tem = list(calendar.monthcalendar(2019, filter_month))
for li in tem:
    days_list += li
days_list = [datetime.strptime("%s/%s/19 00:00" % (filter_month, i), '%m/%d/%y %H:%M').date() for i in days_list if
             i != 0]
for day in days_list:
    if day in station_records[filter_stationID]:
        fr_cnt = station_records[filter_stationID][day]['fromCNT']
        fromCNT_for_each_day.append(fr_cnt)
    else:
        fromCNT_for_each_day.append(0)
days_list = [str(d.day) for d in days_list]
plt.figure(figsize=(30, 20))
plt.bar(days_list,fromCNT_for_each_day)
plt.title('Distribution of bike rentals at station %s in %s' % (filter_stationID, calendar.month_name[filter_month]))
plt.xlabel('Days')
plt.ylabel('FromCNT')
plt.show()

# Task 2.3
# Aggregate fromCNT by hour in all days of that month
hours_list = [i for i in range(0,24)]
total_from_CNT_by_hours = [0]*24
for bike,data in dates_time.items():
    for date,info in data.items():
        if date.month == filter_month:
            if not math.isnan(info[0]):
                total_from_CNT_by_hours[date.hour] += 1
plt.plot(hours_list,total_from_CNT_by_hours,color='black')
plt.title('Distribution of bike rentals throughout the day in %s' % (calendar.month_name[filter_month]))
plt.xlabel('Hours')
plt.ylabel('FromCNT')
plt.show()

# Task 2.4
bike_id_list = [0]*25
rental_counts = dict()
rental_counts_sorted = list()
for bike,data in dates_time.items():
    monthly_count = 0
    for date,info in data.items():
        if date.month == filter_month:
            monthly_count += 1
    if monthly_count != 0:
        rental_counts_sorted.append(monthly_count)
        rental_counts[bike] = monthly_count
rental_counts_sorted = sorted(rental_counts_sorted,reverse=True)[0:25]
tem_list = rental_counts_sorted.copy()
for k,v in rental_counts.items():
    if v in tem_list:
        i = tem_list.index(v)
        bike_id_list[i] = k
        tem_list[i] = 0
bike_id_list = [str(i) for i in bike_id_list]
plt.figure(figsize=(55, 20))
ax = plt.bar(bike_id_list,rental_counts_sorted)
plt.title('25 most popular bikes for %s' % calendar.month_name[filter_month])
plt.xlabel('BikeID')
plt.ylabel('Number of rentals')
plt.show()

# Task 3.1
plt.rcParams.update({'font.size': 10})
rebal_count_list = list()
station_ranking = ['0'] * 25
for sta_id, month_reports in station_records_by_month.items():
    if filter_month in month_reports:
        rebal_count_list.append(month_reports[filter_month]['rebalCNT'])

rebal_count_list.sort(reverse=True)
tem_list = rebal_count_list[0:25].copy()

for id, data in station_records_by_month.items():
    if filter_month in data:
        rebalCNT = data[filter_month]['rebalCNT']
        if rebalCNT in tem_list:
            index = tem_list.index(rebalCNT)
            station_ranking[index] = str(int(id))
            tem_list[index] = 0
plt.figure(figsize=(55, 20))
plt.bar(station_ranking, rebal_count_list[0:25])
plt.title('Most demanding stations for rebalancing in %s' % calendar.month_name[filter_month])
plt.xlabel('StationID')
plt.ylabel('RebalCNT')
plt.show()

# Task 3.2
days_list = []
rebalCNT_for_each_day = []
tem = list(calendar.monthcalendar(2019, filter_month))
for li in tem:
    days_list += li
days_list = [datetime.strptime("%s/%s/19 00:00" % (filter_month, i), '%m/%d/%y %H:%M').date() for i in days_list if i != 0]
for day in days_list:
    if day in station_records[filter_stationID]:
        rebal_cnt = station_records[filter_stationID][day]['rebalCNT']
        rebalCNT_for_each_day.append(rebal_cnt)
    else:
        rebalCNT_for_each_day.append(0)
days_list = [str(d.day) for d in days_list]
plt.figure(figsize=(30, 20))
plt.plot(days_list,rebalCNT_for_each_day,color='blue')
plt.title('Distribution of bike rebalancing at station %s in %s' % (filter_stationID, calendar.month_name[filter_month]))
plt.xlabel('Days')
plt.ylabel('RebalCNT')
plt.show()

# Task 4.1
df3 = pd.DataFrame()
df3['from_cnt_7'] = [data['fromCNT'] if data is not None else 0 for data in df2[7]]
df3['from_cnt_8'] = [data['fromCNT'] if data is not None else 0 for data in df2[8]]
df3['from_cnt_9'] = [data['fromCNT'] if data is not None else 0 for data in df2[9]]
df3['rebal_cnt_7'] = [data['fromCNT'] if data is not None else 0 for data in df2[7]]
df3['rebal_cnt_8'] = [data['fromCNT'] if data is not None else 0 for data in df2[8]]
df3['rebal_cnt_9'] = [data['fromCNT'] if data is not None else 0 for data in df2[9]]
k_means_1 = cluster.KMeans(n_clusters=4, init = 'k-means++',random_state=5000)
data = df3[['from_cnt_7','from_cnt_8','from_cnt_9','rebal_cnt_7','rebal_cnt_8','rebal_cnt_9']]
k_means_1.fit(data)
cluster1 = Counter(k_means_1.labels_)
cluster1_sorted = SortedDict()
cluster1_sorted = cluster1_sorted.fromkeys(cluster1.keys(),cluster1.values)
# Kmean 2
k_means_2 = cluster.KMeans(n_clusters=5, init = 'k-means++',random_state=5000)
k_means_2.fit(data)
cluster2 = Counter(k_means_2.labels_)
# Kmean 3
k_means_3 = cluster.KMeans(n_clusters=6, init = 'k-means++',random_state=5000)
k_means_3.fit(data)
cluster3 = Counter(k_means_3.labels_)

# DBscan 1
DBscan_1 = cluster.DBSCAN(eps=20,min_samples=2).fit(data)
cluster4 = Counter(DBscan_1.labels_)
cluster4.pop(-1)
# DBscan 2
DBscan_2 = cluster.DBSCAN(eps=15,min_samples=3).fit(data)
cluster5 = Counter(DBscan_2.labels_)

# DBscan 3
DBscan_3 = cluster.DBSCAN(eps=18,min_samples=6).fit(data)
cluster6 = Counter(DBscan_3.labels_)
