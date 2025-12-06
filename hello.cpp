#include <iostream>
#include <string>
using namespace std;


int Search(string text, string pattern) {
    int n = text.length();
    int m = pattern.length();

    if (m == 0) 
    return -1; 

    for (int i = 0; i <= n - m; i++) {
        bool match = true;
        for (int j = 0; j < m; j++) {
            if (text[i + j] != pattern[j]) {
                match = false;
                break;
            }
        }
        if (match)
         return i;
    }

    return -1; 
}

int main() {
    string text, pattern;

    cout << "Enter the text:";
    getline(cin, text);

    cout << "Enter the pattern: ";
    getline(cin, pattern);

    int index = Search(text, pattern);

    if (index != -1)
        cout << "Pattern found at index in array : " << index << endl; // commemtss for practce 
    else
        cout << "Pattern not found" << endl;

    return 0;
}
