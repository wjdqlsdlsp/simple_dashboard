import datetime
import os
import boto3

import matplotlib.pyplot as plt
import pandas as pd
import matplotlib.font_manager as fm
AWS_KEY_ID = os.environ.get("AWS_KEY_ID")
AWS_SECRET_KEY = os.environ.get("AWS_SECRET_KEY")
font = fm.FontProperties(fname='DoHyeon-Regular.ttf')

data = pd.read_csv("세상의 모 776cc.csv")
can_handle = data['Name'].dropna().index
data = data.iloc[can_handle].reset_index()

# 날자 처리
data['date'] = data['Name'].apply(lambda x : '20'+str(x).split(']')[0][1:])
data['date'] = pd.to_datetime(data['date'], format='%Y%m%d')
data = data[~data['학습시간'].isna()]
start_date, end_date = datetime.date.today() - datetime.timedelta(days=1), datetime.date.today() - datetime.timedelta(days=7)
data = data[(data['date'] <= pd.to_datetime(start_date)) & (data['date'] >= pd.to_datetime(end_date))]

# # 이름 매핑
name_map = {'Chaewon Lee' : '이채원', '박정빈' : '박정빈', '박승일' : '박승일', 'Captain mycaptain' : '이재훈' }
data['작성자'] = data['작성자'].map(name_map)
data = data[(data['작성자'] == '박정빈') | (data['작성자'] == '이재훈')| (data['작성자'] == '박승일') |(data['작성자'] == '이채원')]

def make_study_time(study_time):
    total_time = 0
    arr = study_time.split(',')
    for i in arr:
        tmp = i.split('~')
        start, end = tmp[0].strip(), tmp[1].strip()
        start = start.split(":")
        start = int(start[0]) * 60 + int(start[1])
        end = end.split(":")
        if end[0] =='':
            continue
        end = int(end[0]) * 60 + int(end[1])
        if end < start:
            end += 60 * 24
        total_time += end - start
    return round(total_time / 60, 1)
data['학습시간'] = data['학습시간'].apply(make_study_time)

arr_tmp = []
for name in ['박승일', '박정빈', '이재훈', '이채원']:
    for i in range(1, 8):
        tmp = datetime.date.today() - datetime.timedelta(days=i)
        tmp_day =pd.to_datetime(tmp)

        if len(data[(data['작성자'] == name) & (data['date'] == tmp_day)]) < 1:
            arr_tmp.append([name, tmp_day, 0])

tmp_pd = pd.DataFrame(arr_tmp)
tmp_pd.columns = ['작성자', 'date', '학습시간']
data = pd.concat([data, tmp_pd],ignore_index=True)

users = [ '박정빈', '이재훈', '박승일','이채원']
colors = ['#79C1E6','#429981','#DD9CE6','#FFB207']

fig, ax = plt.subplots(figsize=(30,15))

xticks_date = data[data['작성자'] == '박정빈']['date']
weekday = ['월', '화', '수', '목', '금', '토', '일']
weekdays1 = [*map(lambda x : str(x)[5:10] + "(" + weekday[x.date().weekday()] + ")" , xticks_date)]
weekdays1 = [*map(lambda x : x.replace("-", "/"), weekdays1)]
weeks_study_time = []

for user, color in zip(users,colors):
    data_user = data[data['작성자'] == user].sort_values(by='date')
    data_user['학습시간'] = data_user['학습시간'].cumsum()
    plt.plot(data_user['date'].values , data_user['학습시간'].values, lw=6, color=color)
    plt.scatter(data_user['date'].values , data_user['학습시간'].values, s=150, color=color)

    tmp_last_loc = data_user.tail(1)
    time = data_user.tail(1)['학습시간'].values[0]
    date = data_user.tail(1)['date'].values[0] + pd.to_timedelta('6 hours')
    weeks_study_time.append([user, round(time,2), date, color, time])

weeks_study_time = sorted(weeks_study_time, key=lambda x: x[1], reverse=True)
for i in range(1, len(weeks_study_time)):
    if weeks_study_time[i][1] > weeks_study_time[i-1][1] - 4:
        weeks_study_time[i][4] = weeks_study_time[i-1][4] - 4

for user, time, date, color, y_position in weeks_study_time:
    plt.text(s=f'{user}', x=date, y = y_position,font=font, fontsize=30, va='center', ha='center', color=color)
    plt.text(s=f'{round(time,2)}시간', x=date, y=y_position-1.7,font=font, fontsize=20, va='center', ha='center', color=color)

plt.gca().spines['left'].set_visible(False)
plt.gca().spines['right'].set_visible(False)
plt.gca().spines['top'].set_visible(False)
plt.grid()

first, end = str(data.head(1)['date'].values)[7:12], str(data.tail(1)['date'].values)[7:12]
first = first.replace('-', '/')
end = end.replace('-', '/')
plt.title(f'일주일간 공부시간 ({end} ~ {first})', font=font, fontsize= 40,pad=32)

plt.ylabel('공부시간 (누적)',font=font, fontsize=30)
plt.xlabel('',font=font, fontsize=30)
plt.xticks([], font=font, fontsize=40)
plt.yticks(font=font,fontsize=40)

for i, v in enumerate(xticks_date):
    plt.text(s=weekdays1[i], x= v, y=-0.5,font=font, fontsize=40, va='top', ha='center')
    plt.axvline(v, color='gray', alpha = 0.5)

plt.ylim(0, )
fig.savefig('my_plot.png')

s3 = boto3.client('s3', region_name='ap-northeast-2',
                        aws_access_key_id=AWS_KEY_ID,
                        aws_secret_access_key=AWS_SECRET_KEY)

s3.upload_file(Bucket='semogong',
              Filename='my_plot.png',
              Key='my_plot.png',
              ExtraArgs={'ACL':'public-read'})