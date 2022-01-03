import logging

import pandas as pd
import numpy as np
import glob
import os

import sys

#sys.path.insert(0, '../3_Hashtag_study')
sys.path.insert(0, '..')

import general_utils as ut
#import hashtag_util as ht_ut

logger = logging.getLogger("main")

workers = 8


def read_all_csv(datapath):
    files = sorted(glob.glob(datapath))
    dfConcat = pd.DataFrame()

    for file in files:
        df1 = pd.read_csv(file, low_memory=False, lineterminator='\n', error_bad_lines=False)
        dfConcat = pd.concat([dfConcat, df1], ignore_index=True)
        print(file, " ", len(df1))
        del df1

    return dfConcat


def concat_base_file(start, file_concat):
    dfStart = pd.read_csv(start, low_memory=False, lineterminator='\n', error_bad_lines=False)
    for file in file_concat:
        df1 = pd.read_csv(file, low_memory=False, lineterminator='\n', error_bad_lines=False)
        dfStart = pd.concat([dfStart, df1], ignore_index=True)
        print(file, " ", len(df1))
        del df1
    return dfStart

def create_cred_score(tweets_with_urls,threshold=10):
    sum_of_urls_df = tweets_with_urls.groupby(['user_id']).sum()
    cred_score_df = sum_of_urls_df[sum_of_urls_df['HIGH']+sum_of_urls_df['LOW']>=threshold]
    scores =  np.around(((cred_score_df['HIGH'])/(cred_score_df['LOW']+cred_score_df['HIGH'])),2)
    return scores.items()
    

def inspect_users(root_folder):
    nf_users_folder = os.path.join(root_folder, 'not_found_users')
    if not os.path.exists(nf_users_folder):
        print("Not found users folder not found!")
        return {}
    nf_users = pd.read_csv(os.path.join(nf_users_folder, 'users_not_found.csv'), lineterminator='\n', usecols=['id'])
    nf_ids = set(nf_users['id'].unique())

    users = pd.read_csv(os.path.join(root_folder, 'users_ids.csv'), lineterminator='\n', usecols=['user_id'])
    users_ids = set(users['user_id'].unique())

    return users_ids.difference(nf_ids)


def process_df_hashtags(df, hashtags):
    dfUsers = ht_ut.process_df_uses_hashtags(df, hashtags)
    dfUsers = dfUsers.groupby('user').any()
    dfUsers = ht_ut.hashtagOR(hashtags, dfUsers)
    return dfUsers[dfUsers['OR']].index


def process_df_url(df, urls):  # TODO real function
    dfUsers = pd.DataFrame()
    return dfUsers.index


def suspect_rate(df):
    df.loc[df['suspect'].isna(), 'suspect'] = 0
    df['rt_rate'] = (df['suspect'] / df['total']) * 100
    return df


def retweeted_by_suspect(df, listSuspect):
    dfTweetsSus = df[df.isin(listSuspect)['user_screen_name']]
    dfRetweeted = dfTweetsSus.groupby('rt_user_screen_name').count()['id']
    return dfRetweeted    


def retweet_a_suspect(df, listSuspect, minRetweet=10):
    dfRetweet = pd.DataFrame()
    dfRetweet['total'] = df.groupby('user_screen_name').count()['rt_user_screen_name']

    dfRetweetSus = df[df.isin(listSuspect)['rt_user_screen_name']]

    dfRetweet['suspect'] = dfRetweetSus.groupby('user_screen_name').count()['id']

    dfRetweet = dfRetweet[dfRetweet['total'] >= minRetweet]

    return suspect_rate(dfRetweet)

def retweet_rate_novax(df, listnovax, listprovax,min_sum_retweet=10):
    dfRetweet = pd.DataFrame()
    
    dfRetweet['novax'] = df[df.isin(listnovax)['rt_user_screen_name']].groupby('user_screen_name').count()['id']
    dfRetweet['provax'] = df[df.isin(listprovax)['rt_user_screen_name']].groupby('user_screen_name').count()['id']
    
    dfRetweet['sum'] = dfRetweet['novax']+dfRetweet['provax']
    dfRetweet = dfRetweet[dfRetweet['sum'] >= min_sum_retweet]
    
    dfRetweet['novax_perc'] = (dfRetweet['novax'] - dfRetweet['provax']) / dfRetweet['sum']
    dfRetweet['provax_perc'] = (dfRetweet['provax'] - dfRetweet['novax']) / dfRetweet['sum']

    return dfRetweet