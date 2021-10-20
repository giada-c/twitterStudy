import logging
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import wait as futures_wait

import numpy as np
import pandas as pd
from itertools import repeat
import re

import plotly.express as px
import plotly.graph_objects as go

import sys

sys.path.insert(0, '../')

import general_utils as gen_ut

logger = logging.getLogger("main")

workers = 8

'''
GRAPHICS VISUALIZATION
'''


def visual_histogram(dfHashtags, *arrayUse):

    arrayUse = sorted(arrayUse, reverse=True)
    for i, numUse in enumerate(arrayUse):

        dfHashtagAbove = dfHashtags.drop(dfHashtags[dfHashtags['count'] < numUse].index)
        if i > 0:
            dfHashtagAbove = dfHashtagAbove.drop(dfHashtags[dfHashtags['count'] > arrayUse[i-1]].index)

        fig = px.histogram(dfHashtagAbove, y=dfHashtagAbove.index, x=dfHashtagAbove['count'],
                           title="Hashtags over " + str(numUse) + " uses", orientation='h')
        fig.show()

    dfHashtagUnder = dfHashtags.drop(dfHashtags[dfHashtags['count'] > numUse].index)
    fig = px.histogram(dfHashtagUnder, y=dfHashtagUnder.index, x=dfHashtagUnder['count'],
                       title="Hashtags under " + str(numUse) + " uses", orientation='h')
    fig.show()


def visual_by_date_together(dfHashtags, dfUse, head_count=10, useHead=True):
    df1 = pd.DataFrame()
    if useHead:
        df1 = dfHashtags.head(head_count)
    else:
        dfHashtags.drop(dfHashtags[dfHashtags['count'] < head_count].index)
    fig = go.Figure()

    for hashtag in df1.index:
        mask = dfUse['hashtag'] == hashtag
        fig.add_trace(go.Scatter(x=dfUse.loc[mask, 'Week/Year'], y=dfUse.loc[mask, 'count'],
                                 mode='lines+markers',
                                 name=hashtag))
    fig.update_layout(title="History use of hashtags", xaxis_title='Date', yaxis_title='use count')
    fig.show()


def visual_by_date_split(dfHashtags, dfUse, head_count=10, useHead=True):
    df1 = pd.DataFrame()
    if useHead:
        df1 = dfHashtags.head(head_count)
    else:
        dfHashtags.drop(dfHashtags[dfHashtags['count'] < head_count].index)

    for hashtag in df1.index:
        mask = dfUse['hashtag'] == hashtag
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dfUse.loc[mask, 'Week/Year'], y=dfUse.loc[mask, 'count'],
                                 mode='lines+markers',
                                 name=hashtag))
        fig.update_layout(title="History use of hashtag '%s'" % hashtag, xaxis_title='Date', yaxis_title='use count')
        fig.show()


'''
COMPLETE DATAFRAME STUDY
'''


def get_line_dfUse(df):
    hashtag = []
    date = []

    for i in df.index:
        d = df.at[i, 'created_at']
        s = df.at[i, 'hashtags']
        for h in gen_ut.get_string_json(s, 'text'):
            hashtag.append(h)
            date.append(d)
    dfUse = pd.DataFrame().from_dict({"hashtag": hashtag, "date": date, "count": list(repeat(1, len(date)))})

    dfUse['Week/Year'] = dfUse['date'].apply(lambda x: "%d-%d" % (x.isocalendar()[1], x.isocalendar()[0]))
    dfUse.drop(['date'], axis=1, inplace=True)

    dfUse = dfUse.groupby(['Week/Year', 'hashtag']).sum()
    dfUse.reset_index(inplace=True)

    dfUse['Week/Year'] = pd.to_datetime(dfUse['Week/Year'] + '-1', format="%W-%Y-%w")

    return dfUse


def process_dfUse(df, worker=workers):
    results = pd.DataFrame()
    executor = ProcessPoolExecutor(max_workers=worker)
    futures = []

    # multiprocess
    subchunks = np.array_split(df, workers)
    for sc in subchunks:
        futures.append(executor.submit(get_line_dfUse, sc))
    futures_wait(futures)
    # waits until all futures are completed
    for fut in futures:
        results = pd.concat([fut.result(), results], ignore_index=True)

    executor.shutdown()
    return results.sort_values(by='Week/Year')


'''
SINGLE HASHTAG STUDY
'''


def hashtagAND(hashtags, df):
    df['AND'] = True
    for i in df.index:
        for h in hashtags:
            if not df.loc[i, h]:
                df.loc[i, 'AND'] = False
    return df


def hashtagOR(hashtags, df, colname='OR', threshold=1):
    df[colname] = False
    for i in df.index:
        numHashtag = 0
        for h in hashtags:
            if df.loc[i, h]:
                numHashtag += 1
                df.loc[i, colname] = numHashtag >= threshold

    return df


def df_uses_hashtags_line(hashtags, df):
    my_dict = {"user": []}
    my_dict.update({h: [] for h in hashtags})
    for i in df.index:
        s = df.at[i, 'hashtags']
        s = s.replace("\'", "\"")
        u = df.at[i, 'user_screen_name']
        for h in gen_ut.get_string_json(s, 'text'):
            for key in hashtags:
                    my_dict[key].append(bool(re.match(key, h.lower())))
            my_dict['user'].append(u)

    return pd.DataFrame.from_dict(my_dict)


def process_df_uses_hashtags(df, hashtags, worker=workers):
    results = pd.DataFrame()
    executor = ProcessPoolExecutor(max_workers=worker)
    futures = []

    # multiprocess
    subchunks = np.array_split(df, workers)
    for sc in subchunks:
        futures.append(executor.submit(df_uses_hashtags_line, hashtags, sc))
    futures_wait(futures)
    # waits until all futures are completed
    for fut in futures:
        results = pd.concat([fut.result(), results], ignore_index=True)

    executor.shutdown()
    return results


'''
STUDY HASHTAG STARTING FROM OTHER
'''


def is_hashtag_used(hashtag, df, worker=workers):
    results = pd.DataFrame()
    executor = ProcessPoolExecutor(max_workers=worker)
    futures = []

    # multiprocess
    subchunks = np.array_split(df, workers)
    for sc in subchunks:
        futures.append(executor.submit(is_hashtag_used_get_line, hashtag, sc))
    futures_wait(futures)
    # waits until all futures are completed
    for fut in futures:
        results = pd.concat([fut.result(), results], ignore_index=True)

    executor.shutdown()
    return results


def is_hashtag_used_get_line(hashtag, df):
    df[hashtag] = False
    for i in df.index:
        s = df.at[i, 'hashtags']
        s = s.replace("\'", "\"")
        for h in gen_ut.get_string_json(s, 'text'):
            if h == hashtag:
                df.at[i, hashtag] = True
    return df


def get_list_hashtag(df):
    listHashtag = []
    for i in df.index:
        s = df.at[i, 'hashtags']
        s = s.replace("\'", "\"")
        for h in gen_ut.get_string_json(s, 'text'):
            listHashtag.append(h)
    dfReturn = pd.DataFrame(listHashtag, columns=['hashtag'])
    dfReturn['count'] = 1
    dfReturn = dfReturn.groupby('hashtag').sum()
    return dfReturn
