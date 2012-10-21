'''
Super lite version of dependency-resolving generator 

# http://stackoverflow.com/questions/108586/topological-sort-recursive-using-generators
'''
def dependencies_iter(dependency_graph, element, get_dependencies_fn, seen):
	if element not in seen:
		seen.add(element)
		yield element
		for dependencies in get_dependencies_fn( dependency_graph, element ):
			for dependency in dependencies_iter(dependency_graph, dependencies, get_dependencies_fn, seen):
				yield dependency

def test():
	# circular refs.
	# not all depends refed in main catalog
	# all OK
	data = {
		'a':['c']
		, 'b':['c']
		, 'c': ['d','e']
		, 'd': ['e','f','g']
		, 'h': ['j','d']
	}

	print [ k for k in dependencies_iter(
		data
		, 'a' # <- element of interest.
		, lambda data, element: data.get(element, [])
		, set()
	)]



"""
   
   Tarjan's algorithm and topological sorting implementation in Python

   Allows sorting strongly-connected element networks
   (http://en.wikipedia.org/wiki/Strongly_connected_component)
   
   by Paul Harrison
   (http://www.logarithmic.net/pfh/blog/01208083168)
   by Dries Verdegem
   http://www.logarithmic.net/pfh-files/blog/01208083168/tarjan.py

   Public domain, do with it as you will

"""
def strongly_connected_components(graph):
	"""
	Find the strongly connected components in a graph using
	Tarjan's algorithm.
	
	graph should be a dictionary mapping node names to
	lists of successor nodes.

	Altered by Dries Verdegem

	Tarjan's Algorithm (named for its discoverer, Robert Tarjan) is a graph theory algorithm
	for finding the strongly connected components of a graph.
	
	Based on: http://en.wikipedia.org/wiki/Tarjan%27s_strongly_connected_components_algorithm
	"""

	index_counter = [0]
	stack = []
	lowlinks = {}
	index = {}
	result = []
	
	def strongconnect(node):
		# set the depth index for this node to the smallest unused index
		index[node] = index_counter[0]
		lowlinks[node] = index_counter[0]
		index_counter[0] += 1
		stack.append(node)
	
		# Consider successors of `node`
		try:
			successors = graph[node]
		except:
			successors = []
		for successor in successors:
			if successor not in lowlinks:
				# Successor has not yet been visited; recurse on it
				strongconnect(successor)
				lowlinks[node] = min(lowlinks[node],lowlinks[successor])
			elif successor in stack:
				# the successor is in the stack and hence in the current strongly connected component (SCC)
				lowlinks[node] = min(lowlinks[node],index[successor])
		
		# If `node` is a root node, pop the stack and generate an SCC
		if lowlinks[node] == index[node]:
			connected_component = []
			
			while True:
				successor = stack.pop()
				connected_component.append(successor)
				if successor == node: break
			component = tuple(connected_component)
			# storing the result
			result.append(component)
	
	for node in graph:
		if node not in lowlinks:
			strongconnect(node)
	
	return result


def topological_sort(graph):
	count = { }
	for node in graph:
		count[node] = 0
	for node in graph:
		for successor in graph[node]:
			count[successor] += 1

	ready = [ node for node in graph if count[node] == 0 ]
	
	result = [ ]
	while ready:
		node = ready.pop(-1)
		result.append(node)
		
		for successor in graph[node]:
			count[successor] -= 1
			if count[successor] == 0:
				ready.append(successor)
	
	return result


def robust_topological_sort(graph):
	""" First identify strongly connected components,
		then perform a topological sort on these components. """

	components = strongly_connected_components(graph)

	node_component = { }
	for component in components:
		for node in component:
			node_component[node] = component

	component_graph = { }
	for component in components:
		component_graph[component] = [ ]
	
	for node in graph:
		node_c = node_component[node]
		for successor in graph[node]:
			successor_c = node_component[successor]
			if node_c != successor_c:
				component_graph[node_c].append(successor_c) 

	return topological_sort(component_graph)


def test_robust():
	# circular refs.
	# not all depends refed in main catalog
	# all OK
	data = {
		'a':['b','c']
		, 'c': ['d','a']
		, 'd': ['e','f','g']
		, 'h': ['j','d']
		, 'j': ['d']
		# , 'b': []
		# , 'e': []
		# , 'f': []
		# , 'g': []
	}

	# print strongly_connected_components(data)
	assert robust_topological_sort(data) == \
		[('c', 'a'), ('b',), ('h',), ('j',), ('d',), ('g',), ('f',), ('e',)]

if __name__ == '__main__':
	test()
	test_robust()