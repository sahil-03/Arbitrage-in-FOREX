'''
Sahil Adhawade
Implementation of Arbitrage in FOREX 

Construct graph of FOREX rates and find negative 
cycles in the graph for arbitrage opportunities.

Credits:
    - run_bellamn_ford()
    - get_all_negative_cycles() 
    inspired by Reasonable Deviations
'''

'''
UPDATE(S): find_missing_weights(all_edges, missing_edges):

    The purpose of this function is to find the missing edge weights and replace the 
    0s in the matrix. This will create a completely connected graph. It will enable
    the algorithm to potentially find more arbitrage opportunities. 

    This feature will come out in version 2...
'''

from collections import defaultdict
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By

import math as math
import networkx as nx 
import numpy as np
import pandas as pd
import time as time

# Global Variables
CURRENCIES = ['eur', 'usd', 'jpy', 'gbp', 'try', 'chf', 'cad', 'aud', 'nzd', 'inr', 'cny', 'sgd', 'hkd', 'dkk', 'sek', 'rub', 'mxn', 'zar']

CURRENCIES_DICT = {0 : 'eur', 1 : 'usd', 2 : 'jpy', 3 : 'gbp', 4 : 'try', 5 : 'chf', 6 : 'cad', 7 : 'aud', 8 : 'nzd', 
9 : 'inr', 10 : 'cny', 11 : 'sgd', 12 : 'hkd', 13 : 'dkk', 14 : 'sek', 15 : 'rub', 16 : 'mxn', 17 : 'zar'}

PAIRS = ['eur-usd', 'usd-jpy', 'gbp-usd', 'usd-try', 'usd-chf', 'usd-cad', 'eur-jpy', 'aud-usd', 'nzd-usd', 'eur-gbp', 'eur-chf', 'aud-jpy', 'gbp-jpy',
'chf-jpy', 'eur-cad', 'aud-cad', 'cad-jpy', 'nzd-jpy', 'aud-nzd', 'gbp-aud', 'eur-aud', 'gbp-chf', 'eur-nzd', 'aud-chf', 'gbp-nzd', 'usd-inr', 'usd-cny', 
'usd-sgd', 'usd-hkd', 'usd-dkk', 'gbp-cad', 'usd-sek', 'usd-rub', 'usd-mxn', 'usd-zar', 'cad-chf', 'nzd-cad', 'nzd-chf']

PAIR_ID = [1,3,2,18,4,7,9,5,8,6,10,49,1,13,16,47,51,58,50,53,15,12,52,48,55,160,2111,42,155,43,54,41,2186,39,17,14,56,57]


def extract_arbitrage(cycle, G, time_stamp):
    
    total_path = 0
    for (p1, p2) in zip(cycle, cycle[1:]):
        total_path += G[p1][p2]['weight']
    arbitrage = np.exp(-total_path) - 1

    currency_cycle = [CURRENCIES_DICT[i] for i in cycle]

    with open('arbitrage_forex_log.txt', 'a') as f:
        f.write('\nTime: ' + time_stamp)
        f.write('\nPath: ' + str(currency_cycle))
        f.write(f'\n{arbitrage*100:.2g}%\n')


def find_arbitrage_opportunities(G, time_stamp):

    if nx.negative_edge_cycle(G):
        print('ARBITRAGE OPPORTUNITY FOUND :)\n')
        for cycle in get_all_negative_cycles(G):
            extract_arbitrage(cycle, G, time_stamp)
    else:
        print('No arbitrage opportunities :(')


def get_all_negative_cycles(G):

    all_negative_cycles = []
    for source in G.nodes():
        all_negative_cycles.append(run_bellman_ford(G, source))

    flattened = [item for sublist in all_negative_cycles for item in sublist]
    return [list(i) for i in set(tuple(j) for j in flattened)]


def run_bellman_ford(G, source):

    N = len(G.nodes())
    d = defaultdict(lambda: math.inf)
    p = defaultdict(lambda: -1)
    d[source] = 0

    for _ in range(N - 1):
        for u,v in G.edges():
            w = G[u][v]['weight']
            if d[u] + w < d[v]:
                d[v] = d[u] + w
                p[v] = u
    
    all_cycles = []
    visited = defaultdict(lambda: False)

    for u,v in G.edges():
        if visited[v]:
            continue
        w = G[u][v]['weight']
        if d[u] + w < d[v]:
            cycle = []
            x = v
            while True:
                visited[x] = True
                cycle.append(x)
                x = p[x]
                if x == v or x in cycle:
                    break
            i = cycle.index(x)
            cycle.append(x)
            all_cycles.append(cycle[i:][::-1])

    return all_cycles


def get_graph(A):

    G = nx.DiGraph(-np.log(A).T)
    return G


def get_adj_matrix(pairs):

    keys_v1 = pairs.keys()
    keys_v2 = []
    for key in keys_v1:
        c1 = key.split('-')[0]
        c2 = key.split('-')[1]
        new_key = c2 + '-' + c1
        keys_v2.append(new_key)

    adj_matrix = []
    missing_edges = []

    for c in CURRENCIES:
        row = []
        for d in CURRENCIES:
            key = c + '-' + d
            if key in keys_v1:
                ask = float(list(pairs[key])[0])
                row.append(ask)
            elif key in keys_v2:
                corrected_key = key.split('-')[1] + '-' + key.split('-')[0]
                ask = float(list(pairs[corrected_key])[0])
                row.append(float(1 / ask))
            else:
                if c != d:
                    missing_edges.append(key)
                row.append(0)
        adj_matrix.append(row)
    
    A = pd.DataFrame(np.array(adj_matrix))
    #A.to_csv('matrix.csv')
    return A


def get_pairs():

    pairs_dict = {}

    option = webdriver.ChromeOptions()
    option.add_argument('--headless')
    option.add_argument('--no-sandbox')
    option.add_argument('--disable-dev-sh-usage')
    driver = webdriver.Chrome('C:\Program Files (x86)\chromedriver.exe', options = option)

    url = 'https://www.investing.com/currencies/streaming-forex-rates-majors'
    driver.get(url)

    for id in PAIR_ID:
        xpath_pair = f'//*[@id="pair_{str(id)}"]/td[2]/a'
        xpath_xr_bid = f'//*[@id="pair_{str(id)}"]/td[3]'
        xpath_xr_ask = f'//*[@id="pair_{str(id)}"]/td[4]'
    
        pair_name = driver.find_element(By.XPATH, xpath_pair).text
        xr_bid = driver.find_element(By.XPATH, xpath_xr_bid).text
        xr_ask = driver.find_element(By.XPATH, xpath_xr_ask).text
    
        if pair_name != None and xr_bid != None and xr_ask != None:
            name = pair_name.split('/')[0].lower() + '-' + pair_name.split('/')[1].lower()
            pairs_dict[name] = {xr_bid, xr_ask}

    driver.quit()

    return pairs_dict


def main():

    start = time.time()
    
    # Testing
    # pairs = get_pairs()
    # A = get_adj_matrix(pairs)
    # G = get_graph(A)
    # print(G.edges())

    while True:
        pairs = get_pairs()
        A = get_adj_matrix(pairs)
        G = get_graph(A)
        find_arbitrage_opportunities(G, str(datetime.now()))
        print("\nRUN-TIME: " + str(time.time() - start) + " seconds.") 
        time.sleep(15)
         
         
if __name__ == '__main__':
    main()