
#define SUM 50
#define NUM_GAMES 1000000

#include <stdio.h>
#include <stdlib.h>

int main(int argc, char **argv)
{
	int results[SUM] = { 0 };
	int i;
	int game;
	for(i = 0; i < SUM; i++)
	{
		for(game = 0; game < NUM_GAMES; game++)
		{
			int sum = 0;
			int tries = 0;
			while(sum < SUM)
			{
				int tempsum = 0;
				while(tempsum < i + 1)
				{
					int dice = rand() % 6;
					if(dice)
						tempsum += dice;
					else
					{
						tempsum = 0;
						break;
					}
				}
				sum += tempsum;
				tries++;
			}
			results[i] += tries;
		}
		printf(".");
		fflush(stdout);
	}
	printf("\n");

	for(i = 0; i < SUM; i++)
	{
		printf("%2d %1.3f\n", i + 1, (float) results[i] / NUM_GAMES);
	}
	return 0;
}
