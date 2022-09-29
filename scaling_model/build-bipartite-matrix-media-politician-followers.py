#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
build-bipartite-matrix-media-politician-followers.py
Purpose: build a bipartite matrix for the network of followers of media and
		 politician accounts.

Parameters: 
    [REQUIRED] --output: Path to an output file.
                              
Author/s: 
 - Andreu Casas | github.com/CasAndreu | a.casassalleras@vunl
 - Bernhard Clemm | github.com/bernhardclemm | b.f.d.clemm@uva.nl
 
"""

#==============================================================================    
# MODULES -- DEPENDENCIES
#==============================================================================
print('Loading packages')
import os
import pandas as pd
import networkx as nx
from networkx.algorithms import bipartite
import argparse
import re
from datetime import datetime
import numpy as np
import random

#==============================================================================    
# COMMAND LINE ARGUMENTS
#==============================================================================
parser = argparse.ArgumentParser()
parser.add_argument('--output', 
                    help='a path to an output file',
                    required = True)
parser.add_argument('--run', 
                    help='a csv with user ids for which to get followers',
                    required = True)
parser.add_argument('--country', 
                    help='a csv with user ids for which to get followers',
                    required = True)
parser.add_argument('--media', 
                    help='a csv with user ids for which to get followers',
                    required = True)
parser.add_argument('--pol', 
                    help='a csv with user ids for which to get followers',
                    required = True)
args = parser.parse_args()
output_path = args.output
run_number = args.run
run_number = str(run_number)
country = args.country
media_path = args.media
pol_path = args.pol

#==============================================================================    
# MAIN
#==============================================================================
print('\nChecking for which accounts we need to build the network graph')
print(str(datetime.now()).split('.')[0])
# - a list of the follower files for the media accounts
media_list = ['{}{}'.format(media_path, x) for x in os.listdir(media_path)]

# - create a dataframe with the numbers of followers of each domain
media_df = pd.DataFrame()
counter = 0
for f in media_list:
	counter += 1
	if (counter % 10 == 0):
		print('\t {}/{}'.format(counter, len(media_list)))
	new_df = pd.read_csv(f)
	outlet = re.sub('.csv', '', f.split('/')[-1])
	new_row = pd.DataFrame({'outlet':outlet, 'fname':f, 'n':len(new_df)},
		index = [0])
	media_df = pd.concat((media_df, new_row))

# - only move forward with those domains that have at least 500 followers
media_df02 = media_df[media_df['n'] > 250]
media_df02 = media_df02.sort_values('n')

# - distinguish between "small" and "big" media accounts, based on a 
#   subjective number of follower threshold
thres = 100000
small_media = list(media_df02[media_df02['n'] < thres]['outlet'])
big_media = list(media_df02[media_df02['n'] >= thres]['outlet'])

# - create a network graph with the followers of small media
Gsmall = nx.Graph()
counter = 0
total = len(small_media)
for account in small_media:
	f = media_df02[media_df02['outlet'] == account]['fname'].iloc[0]
	# - add this account as a node in the network graph. Note that we use the 
	#	'bipartite' argument to keep track that this is a media/politician 
	#	account and NOT a follower. So, "bipartite = 0". We'll use 
	#   "bipartite = 1" for followers
	Gsmall.add_nodes_from([account], bipartite=0)
	# - update counter and report progress
	counter += 1
	print('{}/{}: {}'.format(counter, total, account))
	print(str(datetime.now()).split('.')[0])
	# - read in the followers of this account
	df = pd.read_csv(f, dtype = str)
	print('\t {} followers'.format(len(df)))
	# - if the account has at least 1 follower, proceed
	if len(df) > 0:
		# - create a list of users and add them as new graph nodes
		followers = set(df['follower_id'])
		Gsmall.add_nodes_from(followers, bipartite = 1)
		# - create a list of tuples reflecting the edges between these 
		#   followers and the account they follow. 
		tuple_list = [(follower, account) for follower in followers]
		Gsmall.add_edges_from(tuple_list)
		print('\t {} overall users so far...'.format(Gsmall.number_of_nodes()))

# - now pull the users who at leat follow 10 of the small media accounts
small_intensefollowers = [z for z in Gsmall.nodes if (Gsmall.degree[z] > 10) and
						  (z not in small_media)]

# - initialize a new (final) network graph with the data from these intense
#   followers of small accounts
G = nx.Graph()
# - add edges for the small media accounts we have already explored
G.add_nodes_from(small_media, bipartite = 0)
# - add edges for the intense followers of small accounts
G.add_nodes_from(small_intensefollowers, bipartite = 1)
node_count = G.number_of_nodes()
# - rebuild the edges between these
for follower in small_intensefollowers:
	follower_edges = [(v,c) for c,v in  Gsmall.edges(follower)]
	G.add_edges_from(follower_edges)

# - now proceed with adding followers (and edges) for the big accounts
counter = 0
total = len(big_media)
newsample = []
for account in big_media:
	f = media_df02[media_df02['outlet'] == account]['fname'].iloc[0]
	# - add this account as a node in the network graph. Note that we use the 
	#	'bipartite' argument to keep track that this is a media/politician 
	#	account and NOT a follower. So, "bipartite = 0". We'll use 
	#   "bipartite = 1" for followers
	G.add_nodes_from([account], bipartite = 0)
	# - update counter and report progress
	counter += 1
	print('{}/{}: {}'.format(counter, total, account))
	print(str(datetime.now()).split('.')[0])
	# - read in the followers of this account
	df = pd.read_csv(f, dtype = str)
	print('\t {} followers'.format(len(df)))
	# - first check if the 'intense' followers follow also this account
	#   and if so, add the additional edges to the graph
	if len(df) > 0:
		followers = set(df['follower_id'])
		current_nodes = set(G.nodes)
		intersect = followers & current_nodes
		diffset = followers - current_nodes
		add_edges = [(follower, account) for follower in intersect]
		G.add_edges_from(add_edges)
		# - finally, sample an additional 300 followers that are not yet
		#   yet in the graph and add them to it
		addfollowers_sample = random.sample(diffset, 400)
		G.add_nodes_from(addfollowers_sample, bipartite = 1)
		print('\t number of nodes: {}'.format(G.number_of_nodes()))
		print('\t number of edges: {}'.format(G.number_of_edges()))
		newsample.extend(addfollowers_sample)

# - iterate through the big accounts again and this time build the edges
#   for all the newly sampled users
newsample = set(newsample)
counter = 0
total = len(big_media)
for account in big_media:
	f = media_df02[media_df02['outlet'] == account]['fname'].iloc[0]
	# - update counter and report progress
	counter += 1
	print('{}/{}: {}'.format(counter, total, account))
	print(str(datetime.now()).split('.')[0])
	# - read in the followers of this account
	df = pd.read_csv(f, dtype = str)
	print('\t {} followers'.format(len(df)))
	if len(df) > 0:
		followers = set(df['follower_id'])
		newsample_found = followers & newsample
		tuple_list = [(follower, account) for follower in newsample_found]		
		G.add_edges_from(tuple_list)
		print('\t number of nodes: {}'.format(G.number_of_nodes()))
		print('\t number of edges: {}'.format(G.number_of_edges()))
		del(df)

# - delete graph with info only about small outlets; not needed anymore 
#   plus it take up memory space
del(Gsmall)

# - to make the network graph a bit more dense, as well as to add more 
#   politically meaningful/relevant information. Adding members of Congress
#   as additional top-level accounts, and adding edges between followers and
#   these members of Congress; in contrast to code for US, delete politicians 
#   with very few followers, otherwise graph is not connected

pol_list = ['{}{}'.format(pol_path, x) for x in os.listdir(pol_path)]
counter = 0
total = len(pol_list)
for f in pol_list:
	# - read in the followers of this account
	df = pd.read_csv(f, dtype = str)
	print('\t {} followers'.format(len(df)))
	# - only proceed if account has more than 25 followers:
	if len(df) > 250:
	# -  pull the name of the politician account
		account = re.sub('.csv', '', f.split('/')[-1])
		# - add this additional top-level node to the graph
		G.add_nodes_from([account], bipartite = 0)
		# - first check if the followers follow also this account
		#   and if so, add the additional edges to the graph
		followers = set(df['follower_id'])
		current_nodes = set(G.nodes)
		intersect = followers & current_nodes
		diffset = followers - current_nodes
		add_edges = [(follower, account) for follower in intersect]
		G.add_edges_from(add_edges)
		print('\t number of nodes: {}'.format(G.number_of_nodes()))
		print('\t number of edges: {}'.format(G.number_of_edges()))
		del(df)
	# - report progress
	counter += 1
	print('{}/{}: {}'.format(counter, total, account))
	print(str(datetime.now()).split('.')[0])	


print('\nPulling bipartite matrix from network graph')
print(str(datetime.now()).split('.')[0])
# - pull now the final list of unique followers and unique media/politician 
#   account in the network graph
follower_nodes, account_nodes = bipartite.sets(G)

# - create adjacency matrix from network graph. Make sure that in the first
#   rows and columns we have the followers, and in the last rows and columns
#   the information about the accounts. This way we can easily pull a
#   bipartitie rectangular matrix where each row is a follower and each column
#   is a media/politician account
rowcolnames = list(follower_nodes) + list(account_nodes)
sq_mat = nx.adjacency_matrix(G, rowcolnames)
rect_mat = sq_mat[:len(follower_nodes),len(follower_nodes):]

print('\nOutput bipartite sparse matrix')
print(str(datetime.now()).split('.')[0])
# - save the data about this sparse matrix in a way that can be read later in R
np.savetxt('{}{}-indices-{}.txt'.format(output_path, country, run_number), rect_mat.indices, fmt='%.0f')
np.savetxt('{}{}-pointers-{}.txt'.format(output_path, country, run_number), rect_mat.indptr, fmt='%.0f')
np.savetxt('{}{}-values-{}.txt'.format(output_path, country, run_number), rect_mat.data, fmt='%.0f')

with open('{}{}-rownames-{}.txt'.format(output_path, country, run_number), 'w') as f:
    for item in list(follower_nodes):
        f.write("%s\n" % item)

with open('{}{}-colnames-{}.txt'.format(output_path, country, run_number), 'w') as f:
    for item in list(account_nodes):
        f.write("%s\n" % item)






