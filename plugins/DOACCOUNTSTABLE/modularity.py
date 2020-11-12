import community as community_louvain
import networkx as nx
import sys

G = nx.read_weighted_edgelist(sys.argv[1])

# compute the best partition
partition = community_louvain.best_partition(G)

for n in partition.keys() :
    print(n,"\t",partition[n])
