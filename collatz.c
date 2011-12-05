
#include <stdio.h>

#define START 1
#define END 1000000
#define REPORT 100000

typedef unsigned long int NUM;

NUM collatz_length(NUM number)
{
	int result = 1;
	while(number != 1)
	{
		if(number % 2 == 0)
			number /= 2;
		else
			number = number * 3 + 1;
		result++;
	}
	return result;
}

int main(int argc, char **argv)
{
	int max_length_index = START;
	int max_length = collatz_length(max_length_index);
	int i;
	for(i = START + 1; i < END; i++)
	{
		int length = collatz_length(i);
		if(length > max_length)
		{
			max_length = length;
			max_length_index = i;
			printf("new max collatz length %d with index %d\n", max_length, max_length_index);
		}
		if(i % REPORT == 0)
		{
			printf("done with %d numbers\n", i);
		}
	}
	printf("max collatz length %d with index %d\n", max_length, max_length_index);
}

