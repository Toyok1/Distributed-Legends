
#include "menu.h"

//using namespace std;

Menu::Menu(){
    setX(5);
    setPlayer_n(2);
    setMode(false);
}

 Menu::Menu(int pn, bool mo){
     setX(5);
     if(pn>=2) 
	setPlayer_n(pn);
     else
	setPlayer_n(2);
     setMode(mo);
 }

void Menu::setX(int x){
    this->x=x;
}
void Menu::setPlayer_n(int n){
    this->Player_n = n;
}
void Menu::setMode(bool n){
    this->Mode=n;
}


int Menu::getX(){
    return this->x;
}
int Menu::getPlayer_n(){
    return Player_n;
}
bool Menu::getMode(){
    return Mode;
}

void Menu::displayAll(){
   cout<< "MODE = "<< getMode() << endl<<"Press any key to continue. . . ";
   getchar();getchar();
   system("clear");
    
}




void Menu::display(){
	system("clear");
	cout<<"  ___   ____   ___"<<endl;
	cout<<" |  _| |    | |   | "<<endl;
	cout<<" | |_  |    | | |)|"<<endl;
	cout<<" | | | |    | |  / "<<endl;
	cout<<" |___| |____| |_|    "<<endl<<endl;

	cout <<"Menu" <<endl;
	cout <<" New Game		(1)" <<endl;
	cout <<" Options		(2)" <<endl;
	cout <<endl <<"Exit Game	(3)"<<endl;
}

void Menu::choice(){
    std::string tmp ="";
    int i_tmp=3;
	switch(this->x){
		case 1:
			//New Game
            		break;
		case 2:
			system("clear");
			this->setOptions();
			break;
		//Exit the game
		case 3:
			while ((i_tmp!=1)&&(i_tmp!=2)){
				cout <<"Are you sure you want to exit GOP?" <<endl <<"(1) Yes" <<endl <<"(2) No"<<endl;
				getline(cin,tmp);
                i_tmp=atoi(tmp.c_str());
				switch(i_tmp){
					case 1:
						system("clear");
						cout <<"Thanks for playing GOP, see you next time" <<endl;
						cout <<"Press any key to continue . . .";
						getchar();system("clear");
						exit(1);
						break;
					case 2:
						system("clear");
						break;
					default:
						cout <<"Wrong input, please select (0) for Yes or (1) for No" <<endl;
						break;
				}
			}
            break;
        default:
            cout << "Not valid!" <<endl<<"Press any key to continue . . .";
			getchar();
			system("clear");
            break;
	}
}

void Menu::setOptions(){
    std::string s_c="";
    int c;
    while (true){
        cout << "OPTIONS" << endl << endl;
        cout << "Difficulty             (1)"<<endl;
        cout << "Rules                 (2)"<<endl;
        cout << "Credits                (3)"<<endl<<endl;
        cout << "Main Menu       (4)"<<endl<<endl;
        
        //input handled with cin, it hallows multiples input by spacing them with blanks, that can facilitates the option settings
        cin >> s_c;
        c=atoi(s_c.c_str());
        switch (c) {
            case 1:
                //casted from int to bool: if the value is 0 the modality will be EASY, in all other cases it will be hard.
                int c;
                s_c="";
		system("clear");
                cout << "DIFFICULTY'" << endl;
                cout << "0) EASY " << endl << "1) HARD"<<endl;
				cout << "In casae of a bad input, the default value of EASY will be chosen."<<endl;
                cin >> s_c;
                if (s_c=="0"||s_c=="1"){
				c=atoi(s_c.c_str());
                setMode((bool)c);
                if (getMode())
                    cout << "HARDCORE MODE" << endl<<"Press any key to continue . . ."<<endl;
                else cout << "EASY MODE" << endl<<"Press any key to continue . . ."<<endl;
        getchar();getchar();
		system("clear");
		break;
			}
			cout << "Default difficulty EASY MODE activated."<<endl<<"Press any key to continue . . ."<<endl;
			getchar();getchar();
			system("clear");
			break;
        
            case 2:
		system("clear");
		this->parseFile("RULES.txt");
		system("clear");
		break;
        
            case 3:
		system("clear");
		this->parseFile("AUTHORS.txt");
		system("clear");
		break;
        
            case 4:
		system("clear");
                cout<<"THESE ARE THE ACTIVE OPTIONS AT THE MOMENT:"<<endl;
                this->displayAll();
                return;
		break;
        
            default:
                cout << "TO ERR IS HUMAN, TO PERSERVERE IS AS WELL."<<endl<<"Press any key to continue . . .";
		getchar();getchar();
		system("clear");
                break;
            }
        }
}

void Menu::parseFile(string name){
	this->file_in.open(name);
	if(!(this->file_in))
		cout <<"Error while opening a file, please check if file " << name <<" exists" <<endl ;
	else{
		cout << "The file is Open . . ." <<endl <<name <<endl <<endl;
		//parse the file
		while(!this->file_in.eof()){
			this->file_in.get(parser);
			cout << this->parser;}
		//this->parser='\';
		this->file_in.close();
	}
	cout <<endl <<"Press any key to continue . . .";
	getchar();getchar();	
}

