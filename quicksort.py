
def qsort(array):
	if len(array) <= 1:
		return array

	pivot = array[0]

	i = 1
	k = len(array) - 1

	while i < k:
		swap = True
		if array[i] <= pivot:
			i += 1
			swap = False

		if array[k] >= pivot:
			k -= 1
			swap = False

		if swap:
			array[i], array[k] = array[k], array[i]

	if array[i] <= pivot:

		return qsort(array[1:i + 1]) + [pivot] + qsort(array[i + 1:])
	else:
		return qsort(array[1:i]) + [pivot] + qsort(array[i:])

def qsort2(iterable):
	if len(iterable) <= 1:
		return iterable

	lesser = []
	greater = []

	pivot = None

	for x in iterable:
		if pivot:
			if x <= pivot:
				lesser.append(x)
			else:
				greater.append(x)
		else:
			pivot = x

	return qsort2(lesser) + [pivot] + qsort2(greater)

