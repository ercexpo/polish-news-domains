#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
01-get-twitter-followers.py
Purpose: get the twitter followers of a list of twitter screen names.
[This file is based on an earlier version "01-get-twitter-followers.py"]
Parameters: 
    [REQUIRED] --input:       A csv with user ids for which to get their list 
                                of followers
    [REQUIRED] --output:      An output directory where to write out the list 
                                of followers       
    [REQUIRED] --keypath:     The path where the keys are located
    [REQUIRED] --colname:     The name of the column containing Twitter handles
    [OPTIONAL] --summarypath: The path where to save a file summarizing the 
                                info pulled for all users
                              
Author/s: 
 - Andreu Casas | github.com/CasAndreu | a.casassalleras@vunl
 - Bernhard Clemm | github.com/bernhardclemm | b.f.d.clemm@uva.nl
 
Example:
python 01-get-twitter-followers.py \
    --input /Users/andreu/Desktop/repos/vu_dutch_election2021/data/elite-handles-twitter-ALL.csv \
    --output /Users/andreu/Desktop/vu_dutch_election2021_DATA/elite_followers/ \
    --keypath /Users/andreu/keys/ \
    --colname twitter \
    --summarypath /Users/andreu/Desktop/vu_dutch_election2021_DATA/summary-get-followers-elites02.csv
"""
#==============================================================================    
# MODULES -- DEPENDENCIES
#==============================================================================
import pandas as pd
import tweepy
import argparse
import pickle
import random
import time
import os
import re
import ast

#==============================================================================    
# CONSTANTS
#==============================================================================

# Add list of keys here
# KEYS = 

#==============================================================================    
# PARSING COMMAND LINE ARGUMENTS
#==============================================================================
parser = argparse.ArgumentParser()
parser.add_argument('--output', 
                    help='a path where to output the list of followers',
                    required = True)
parser.add_argument('--input', 
                    help='a csv with user ids for which to get followers',
                    required = True)
parser.add_argument('--keypath', 
                    help='The path where the keys are located',
                    required = True)
parser.add_argument('--colname', 
                    help='Name of variable containing twitter handles',
                    required = True)
parser.add_argument('--summarypath', 
                    help='The path where to save a summary file',
                    required = False)
args = parser.parse_args()
input_file = args.input
#input_file = '/Users/andreu/Desktop/repos/vu_dutch_election2021/data/elite-handles-twitter-ALL.csv'
output_path = args.output
#output_path = '/Users/andreu/Desktop/vu_dutch_election2021_DATA/elite_followers/'
keys_path = args.keypath
#keys_path = '/Users/andreu/keys/'
sumpath = args.summarypath
#sumpath = '/Users/andreu/Desktop/vu_dutch_election2021_DATA/summary-get-followers-elites01.csv'
tw_colname = args.colname
#tw_colname = 'twitter'

#==============================================================================    
# MAIN
#==============================================================================
def main():
    print('Loading data')
    # - read the input file (csv)
    db = pd.read_csv(input_file)
    
    # - count the number of twitter keys to use
    max_keys = len(KEYS)
    print('Using {} keys.'.format(max_keys))
    
    # - connect to twitter API
    key_name = random.choice(KEYS)
    api = connect_to_twitter_api(keys_path, key_name)
    
    # - create unique list of users
    users = list(set(list(db[tw_colname].dropna())))
    users = [re.sub('@', '', x) for x in users]
    users_n = len(users)
    print('{} users. Pulling followers and saving the output in: {}.'.format(
            users_n, output_path))
    
    # - initializing a data object summarizing info for all users
    sumdb = []
    
    # - a list of the users for which we have already downloaded their followers
    #   and so for which we have already a csv in the data output directory
    users_done = os.listdir(output_path)
    if len(users_done) > 0:
        users_done_lower = [x.split('.')[0].lower() for x in users_done]
    else:
        users_done_lower = users_done
    
    # - iterate through users, pull followers, and save output
    user_counter = 0
    for user in users:
        user_counter += 1
        print('\t user {}/{}: {}'.format(
                user_counter, users_n, user))
        # - initializing a data object with summary info for this user
        user_sum = {}
        user_sum['user'] = user
        # - check if already downloaded this user's followers
        outname = '{}{}.csv'.format(output_path, user)
        already_done = user.lower() in users_done_lower
        
        if already_done:
            print('\t\t already collected followers. Moving to next user.')
            matched_user = [users_done[i] for i in range(0,len(users_done))
                       if users_done_lower[i] == user.lower()][0]
            prev_outname = '{}{}'.format(output_path, matched_user)
            collected_df = pd.read_csv(prev_outname)
            user_sum['followers_n'] = len(collected_df )
            user_sum['exists'] = 1
        else:                            
            # - check first if screen_name exists
            print('\t\t checking if user exists.')
            verify_tries = 0
            verify_done = False
            while not verify_done:
                key_name = random.choice(KEYS)
                api = connect_to_twitter_api(keys_path, key_name)
                verify_tries += 1
                try:
                    user_info = api.get_user(user)
                    followers_count = user_info._json['followers_count']
                    exists = True
                    verify_done = True
                    del(user_info)
                    print('\t\t users DOES exist.')
                except tweepy.TweepError as error:
                    print(error)
                    error = ast.literal_eval(str(error))
                    # - check error is not just because key/Twitter not operative
                    if error[0]['code'] in [88, 32, 89, 130, 503]:
                        if verify_tries < max_keys:
                            print('\t\t {}{}'.format(
                                    'key/server issues. ',
                                    'Sleeping 5 secs and connecting using another key'))
                            time.sleep(5)
                        else:
                            print('\t\t {}{}'.format(
                                    'have tried all keys already. ',
                                    'Sleeping 60 secs and trying again.'))
                            verify_tries = 0
                    else:
                        exists = False
                        verify_done = True
                        print('\t\t users DOES NOT exist. Moving to next user.')
            user_sum['exists'] = int(exists)
            
            # - if the user exists, pull followers, and save output
            if exists:            
                user_followers = get_followers(user = user,
                                             followers_count = followers_count,
                                             keys_path = keys_path,
                                             keys_list = KEYS)
                # - transform all folloer ids to strings
                if len(user_followers) > 0:
                    user_followers = [str(x) for x in user_followers]
                user_sum['followers_n'] = len(user_followers)
                # - write out a csv with the followers of this user
                out_db = pd.DataFrame({'follower_id':user_followers})            
                out_db.to_csv(outname, index = False)
            else:
                user_sum['followers_n'] = None
        # - update summary info for all users
        sumdb.append(user_sum)
    # - if path to a summary file provided, outputing one
    if sumpath:
        if len(sumdb) == 1:
            sumdf = pd.DataFrame(sumdb, index = [0])
        else:
            sumdf = pd.DataFrame(sumdb)
        sumdf.to_csv(sumpath, index = False)
        

#==============================================================================    
# FUNCTIONS
#==============================================================================
def connect_to_twitter_api(keys_path, key_name):
    """
    This function connets to the Twitter API via tweepy and returns an API
    object.
    
    'keys_path' = (string)  Path where your key is located
    'key_name' = (string)   Name of the key object. Pickle file containing a
                            dictionary with the following keys: 'ckey', 
                            'csecret', 'atoken', and 'asecret'.
    """
    # - import pickle file with the key
    key = pickle.load(open('%s%s'%(keys_path, key_name), 'rb'))
    auth = tweepy.OAuthHandler(key['consumer_key'],key['consumer_secret'])
    auth.set_access_token(key['access_token'],key['access_token_secret'])
    api = tweepy.API(auth)
    return(api)    
    
    
def get_followers(user, followers_count, keys_path, keys_list):
    """
    Returns a list of all followers by this user
    
    'user' = (string)       A Twitter 'screen_name'
    'followers_count' = (int) Number of followers to collect for this user
    'keys_path' = (string)  Path where your key is located
    'key_name' = (string)   Name of the key object. Pickle file containing a
                            dictionary with the following keys: 'ckey', 
                            'csecret', 'atoken', and 'asecret'.
    """    
    # - initialize some necessary variables and data obects
    max_keys = len(keys_list)
    done = False        
    followers_ids = []
    page_num = 0
    keys_used = 0
    key_i = 0    
    
    while not done: 
        # - try to pull the Followers' IDs, if Rate Limit Error, switch key.
        try:
            # - connect to the API
            # - start always trying with the first key of the list
            key_name = KEYS[key_i]
            print(key_name)
            api = connect_to_twitter_api(keys_path, key_name)
            keys_used += 1
            
            # - if we are just starting to pull this user's followers, start
            #   from frist 'page'
            if page_num == 0:
                cursor = tweepy.Cursor(api.followers_ids, id = user)
            # - otherwise, start from the page in which you got the rate limit
            else:
                cursor = tweepy.Cursor(api.followers_ids, id = user, 
                                       cursor = next_cursor)
            # - iterate through the pages in this cursor and pull 5,000 
            #   followers at a time
            for page in cursor.pages():                
                followers_ids.extend(page)
                print('\t\t ... + {}: {}/{}'.format(len(page), len(followers_ids),
                      followers_count))
                # - keeping track of the "page", so we can re-start from there 
                #  if needed (if time limit reached in the middle)
                next_cursor = cursor.iterator.next_cursor
                page_num += 1
            done = True
        except tweepy.TweepError as error:
            print(error)
            # 
            if 'Not authorized' in str(error) or '401' in str(error):
                # - this means this user is protected and we can't get its 
                #   followers list
                done = True
            else:
                error = ast.literal_eval(str(error))
                # - if it's a Rate Limit error, switch keys and/or wait)
                if error[0]['code'] in [88, 32, 89, 130, 503]:
                    # - if still some keys to try, switch, otherwise sleep 60 secs
                    if keys_used < max_keys:
                        print('\t\t reached limit for key {}. Using next key'.format(
                                key_name))
                        key_i += 1
                        #keys_used += 1
                    else:
                        print('\t\t all keys are exhausted. Sleeping for 60 secs.')
                        time.sleep(60)
                        key_i = 0
                        keys_used = 0
                else:
                    done = True
    return(followers_ids)
    
if __name__ == "__main__":
    main()