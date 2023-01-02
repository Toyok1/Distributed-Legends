#ifndef GOP_DEF
#define GOP_DEF
#include <iostream>
#include <cstdlib>
#include <stdio.h>
#include <cstring>
#include <string>
#include <sstream>
#include <ctime>
#include <fstream>
#include "game.h"
#define const INT_MAX 5;
#endif

using namespace std;

int main(){
    srand(time(NULL));
    std::string input;
    int menuOption;
    //defining structures needed for the game
    //Menu is the static structure used to select game's options
    //Game is the dinamic structure where actually runs the game
    Menu menu;
    Game *game;
    cout <<"Welcome to GOP! (Gioco dell'Oca Pazza)" <<endl;
    //The menu will continues to show up until the user will choice to exit the game (q)
    
    while(true){
	system("clear");
	menu.display();
        //the input is made parsing a string to an integer so we can handle input errors
        //not valid string (not numbers) will not be accepted
        //string relatives to double/float values will take as integer (casting by truncation)
        getline(cin,input);
        menuOption=atoi(input.c_str());
        menu.setMenuOption(menuOption);
        menu.choice();
	
	//If the user has choice New Game
	if(menu.getX()==1){
		system("clear");
		//the static attributes are setted by the user or default
		//Now, creating the data structures for the game
		cout <<"Number of players " <<endl <<"the default number is 2 and it will stay as the selected number in case of a bad input"<<endl <<"Insert Here: " ;
		getline(cin,input);
		menuOption=atoi(input.c_str());
		cout <<"The game has started, have fun!" <<endl <<"Press any key to continue . . .";
		getchar();
		system("clear");
		game = new Game(menuOption,menu.getMode());
		game->gameStart();
	}

    }
}
