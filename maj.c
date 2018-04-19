#include <stdio.h>

void main() {
	char c = getchar();
	while(c != EOF) {
		if(c >= 'a' && c <= 'z') {
			putchar(c - 32);
		} else {
			putchar(c);
		}
	}
}