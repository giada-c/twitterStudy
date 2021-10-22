import logging
from concurrent.futures import ProcessPoolExecutor
from concurrent.futures import wait as futures_wait

import numpy as np
import pandas as pd
import re
from collections import Counter

import nltk

nltk.download('stopwords', quiet=True)
from nltk.corpus import stopwords

import it_core_news_sm

import plotly.express as px
import plotly.graph_objects as go

logger = logging.getLogger("main")

workers = 8

'''
GRAPHICS VISUALIZATION
'''


def visual_histogram(df, *arrayUse):
    arrayUse = sorted(arrayUse, reverse=True)
    for i, numUse in enumerate(arrayUse):

        dfTextAbove = df.drop(df[df['count'] < numUse].index)
        if i > 0:
            dfTextAbove = dfTextAbove.drop(df[df['count'] > arrayUse[i - 1]].index)

        fig = px.histogram(dfTextAbove, y='word', x=dfTextAbove['count'],
                           title="Words over " + str(numUse) + " uses", orientation='h')
        fig.show()


'''    dfTextUnder = df.drop(df[df['count'] > numUse].index)
    fig = px.histogram(dfTextUnder, y='word', x=dfTextUnder['count'],
                       title="Words under " + str(numUse) + " uses", orientation='h')
    fig.show()'''


def visual_by_date_together(dfUseWords):
    fig = go.Figure()

    for w in dfUseWords.groupby('word').count().index:
        mask = dfUseWords['word'] == w
        fig.add_trace(go.Scatter(x=dfUseWords.loc[mask, 'Week/Year'], y=dfUseWords.loc[mask, 'count'],
                                 mode='lines+markers',
                                 name=w))
    fig.update_layout(title='All words history use', xaxis_title='Date', yaxis_title='use count')

    fig.show()


def visual_by_date_split(dfUseWords):
    for w in dfUseWords.groupby('word').count().index:
        mask = dfUseWords['word'] == w
        fig = go.Figure(go.Scatter(x=dfUseWords.loc[mask, 'Week/Year'], y=dfUseWords.loc[mask, 'count'],
                                   mode='lines+markers',
                                   name=w))
        fig.update_layout(title="'%s' history use" % w, xaxis_title='Date', yaxis_title='use count')

        fig.show()


'''
WORD COUNT
'''


def lines_df_count(df):
    wordlist = []
    stop_words = set(stopwords.words("italian"))
    # nlp = it_core_news_sm.load()

    for text in df['text']:
        for w in text.split():
            w = w.lower()
            if "#" in w or "@" in w or "http" in w:
                continue

            w = re.sub('[^a-zA-Z\u00C0-\u00FF0-9]+', '', w)

            if w in stop_words:
                continue
            if w == ' ' or w == '':
                continue
            # w = nlp(w)[0].lemma_ #--> too slow
            wordlist.append(w.lower())

    return wordlist


def process_df_count(df, worker=workers):
    results = []
    executor = ProcessPoolExecutor(max_workers=worker)
    futures = []

    # multiprocess
    subchunks = np.array_split(df, workers)
    for sc in subchunks:
        futures.append(executor.submit(lines_df_count, sc))
    futures_wait(futures)
    # waits until all futures are completed
    for fut in futures:
        results += fut.result()

    executor.shutdown()

    dfWords = pd.DataFrame()
    df1 = pd.DataFrame.from_dict(Counter(results), orient='index').reset_index()
    dfWords['word'] = df1.iloc[:, 0]
    dfWords['count'] = df1.iloc[:, 1]

    return dfWords.sort_values(['count'], axis=0, ascending=False)


'''
WORDS USE
'''


def lines_df_use(df, mostUsedWords):
    my_dict = {"word": [], "date": [], "count": []}

    for i in df.index:
        text = df.loc[i, 'text']
        date = df.loc[i, 'created_at']
        for w in text.split():
            if w in mostUsedWords:
                my_dict["word"].append(w)
                my_dict["date"].append(date)
                my_dict["count"].append(1)

    dfUseWords = pd.DataFrame.from_dict(my_dict)

    return dfUseWords


def process_words_use(df, words, worker=workers):
    results = pd.DataFrame()
    executor = ProcessPoolExecutor(max_workers=worker)
    futures = []

    # multiprocess
    subchunks = np.array_split(df, workers)
    for sc in subchunks:
        futures.append(executor.submit(lines_df_use, sc, words))
    futures_wait(futures)
    # waits until all futures are completed
    for fut in futures:
        results = pd.concat([fut.result(), results], ignore_index=True)

    executor.shutdown()

    dfUseWords = results.copy()

    dfUseWords['Week/Year'] = dfUseWords['date'].apply(lambda x: "%d-%d" % (x.isocalendar()[1], x.isocalendar()[0]))
    dfUseWords.drop(['date'], axis=1, inplace=True)

    dfUseWords = dfUseWords.groupby(['Week/Year', 'word']).sum()
    dfUseWords.reset_index(inplace=True)

    dfUseWords['Week/Year'] = pd.to_datetime(dfUseWords['Week/Year'] + '-1', format="%W-%Y-%w")
    dfUseWords.sort_values(['Week/Year'], axis=0, inplace=True, ascending=True)

    return dfUseWords
