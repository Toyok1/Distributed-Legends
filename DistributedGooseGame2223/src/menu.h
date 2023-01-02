/*
 * Description: Header file of class Menu
 */

#ifndef GOP_DEF
#define GOP_DEF
#include <string>
#include <iostream>
#include <fstream>
#include <cstring>
#include <string>
#endif

using namespace std;

class Menu
{
protected:
    int menuOption;   // The menu option
    int playerAmount; // Number of players (>1)
    bool mode;        // difficulty parameter false = EASY || true = HARD
    ifstream file_in; // stream for input file
    char parser;      // string for parsing files

public:
    /* Default Constructor: default configuration:
     * menuOption=
     * PlayerAmount=2;                  will be setted in NewGame menu option
     * sound = true;
     * Mode = false;
     */
    Menu();
    Menu(int playerAmount, bool mode);

    // set methods
    void setMenuOption(int menuOption);
    void setPlayerAmount(int playerAmount);
    void setMode(bool mode);

    // get methods
    int getMenuOption();
    int getPlayerAmount();
    bool getMode();
    void displayAll();

    // display the menu options
    void display();

    // switch the choice of user
    void choice();

    // setting options inside the menu
    void setOptions();

    // parsing input files method
    void parseFile(string name);
};
