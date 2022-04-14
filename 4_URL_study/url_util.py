import logging
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import wait as futures_wait

import numpy as np
import pandas as pd
from itertools import repeat
import re

from plotly.subplots import make_subplots
import plotly.express as px
import plotly.graph_objects as go

import sys

sys.path.insert(0, '../')

import general_utils as gen_ut

logger = logging.getLogger("main")

workers = 8
url_compressed = ['ift.tt', 'dlvr.it', 'bit.ly', 'huffp.st', 'zpr.io', 'ow.ly', 'trib.al', 'is.gd', 'agi.it']
url_grouped = {'youtu.be': 'youtube.com', 'csera.it': 'corriere.it', 'lnkd.in': 'linkedin.com', 'fanpa.ge': 'fanpage.it',
               'rep.repubblica.it': 'repubblica.it'}

def df_url_counter(df):
    listUrls = []
    for s in df['urls']:
        urls = gen_ut.get_string_json(s, 'display_url')
        for url in urls:
            if url:
                url = url.split("//")
                url = url[0].split("/")
                url = url[0]
                if url not in url_compressed:
                    url_decompressed = url_grouped.get(url, False)
                    if url_decompressed:
                        listUrls.append(url_decompressed)
                    else:
                        listUrls.append(url)

    dfUrls = pd.DataFrame()
    dfUrls['url'] = listUrls
    dfUrls['count'] = 1

    dfUrls = dfUrls.groupby('url').sum()
    dfUrls.sort_values(['count'], axis=0, inplace=True, ascending=False)

    return dfUrls


def url_credibility(fileCredibility, dfUrls):
    dfCredibility = pd.read_csv(fileCredibility)
    dfCredibility = dfCredibility.groupby('Domain').first()

    dfUrls['Class'] = dfCredibility['Class']
    dfUrls.sort_values(['count'], axis=0, inplace=True, ascending=False)

    dfUrls.loc[dfUrls['Class'].isna(), 'Class'] = 'none'
    return dfUrls


def get_line_dfUse(df):
    urls = []
    date = []

    for i in df.index:
        d = df.at[i, 'created_at']
        s = df.at[i, 'urls']
        url = gen_ut.get_string_json(s, 'display_url')
        if url:
            url = url[0].split("//")
            url = url[0].split("/")
            urls.append(url[0])
            date.append(d)
    dfUse = pd.DataFrame().from_dict({"url": urls, "date": date, "count": list(repeat(1, len(date)))})

    dfUse['Week/Year'] = dfUse['date'].apply(lambda x: "%d-%d" % (x.isocalendar()[1], x.isocalendar()[0]))
    dfUse.drop(['date'], axis=1, inplace=True)

    dfUse = dfUse.groupby(['Week/Year', 'url']).sum()
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

'''''''''''''''''''''''''Youtube study'''''''''''''''''''''''''''''''

def get_dfYt_line(df,yt_link):
    dfReturn = df.copy()
    dfReturn['yt'] = False
    for i in dfReturn.index:
        urls = gen_ut.get_string_json(dfReturn.loc[i,'urls'], 'expanded_url')
        dfReturn.loc[i,'yt'] = any(item in yt_link for item in urls)
    return dfReturn

'''def get_dfYt_line(df,yt_link):
    dfReturn = df.copy()
    dfReturn['is_yt'] = False
    for i in dfReturn.index:
        dfReturn.loc[i,'is_yt'] = 'youtu' in dfReturn.loc[i,'urls']
    return dfReturn'''


def process_dfYoutube(df, yt_link,worker=workers):
    results = pd.DataFrame()
    executor = ProcessPoolExecutor(max_workers=worker)
    futures = []

    # multiprocess
    subchunks = np.array_split(df, workers)
    for sc in subchunks:
        futures.append(executor.submit(get_dfYt_line,sc, yt_link))
    futures_wait(futures)
    # waits until all futures are completed
    for fut in futures:
        results = pd.concat([fut.result(), results], ignore_index=True)

    executor.shutdown()
    return results