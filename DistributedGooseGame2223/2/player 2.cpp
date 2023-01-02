#include "player.h"


//Default constructor-> only for sentinel element 
Player::Player(){	
	this->next=NULL;
	this->setName("");
	this->setAge(0);
	this->setTurn(-1);
	this->position=NULL;
	this->setNBox(1);
}

//Constructor with parameters
Player::Player(string n, int a, Box *p){
	this->next=NULL;
	this->setName(n);
	this->setAge(a);
	this->setTurn(0);
	this->position=p;	//set her the start cell
	this->setNBox(1);
}

//Setters
void Player::setName(string n){
	this->name=n;
}

void Player::setAge(int a){
	this->age=a;
}

void Player::setTurn(int t){
	this->turn=t;
}

void Player::setNBox(int x){
	this->nBox=x;
}

void Player::setDice(int n){
	this->d=n;
}
//implents here the set cell method

//Getters
string Player::getName(){
	return this->name;
}

int Player::getAge(){
	return this->age;
}

int Player::getTurn(){
	return this->turn;
}

int Player::getNBox(){
	return this->nBox;	
}

int Player::getDice(){
	return this->d;
}
//implements here the get cell method


void Player::Turn(Mazzo *m){
	cout<< "IT'S "<<this->getName()<<"\'S TURN!"<<endl;
	cout << "Press Enter to roll the dice . . .";
	getchar();
	this->setDice(this->dice());
	this->move(this->getDice(),false);
	cout<<"WOW! you rolled a "<<this->getDice()<<endl;
	this->action(m);
	cout << "END OF " <<this->getName()<<"\'S TURN! PRESS ENTER!";
	getchar();
	system("clear");
}

int Player::dice(){
int x;
x=rand()% 6 + 1;
return (x+rand()%6+1);
}

void Player::move(int x, bool v){	//if v is 0, move straight, else move backward
//takes a player and moves its pointer to the apopropriate box one at the time
//updates the position and nBox parameters
	for(x; x>0; x--){
		if ((this->position->getId() != 1)&&(!v)){	
			//go forward if it's not the final square AND v is false
			this->position= this->position->next;
			this->setNBox(this->getNBox()+1);
		}
		else if (this->position->prev!=NULL){					
			this->position=this->position->prev;
			this->setNBox(this->getNBox()-1);
			v=true;
		}
	}
}

//now implements the action method for each subclass
void Player::action(Mazzo *m){
	Box *curr=this->position;	//saving position before action
	Carte c;
	this->position->display();
	switch(this->position->getId()){
		case 3:	//Draw Box
			//cout <<m->getSegnalino();getchar();
			c=m->Pesca();
			c.messaggio();
			this->handleCard(c,m);
			break;		
		case 4:	//Bridge Box
			//Call movement to the player
			this->move(this->getDice(),false);
			break;
		case 5:	//Prison Box
			this->setTurn(3);
			break;
		case 6:	//Inn Box
			this->setTurn(1);
			break;
		case 7:	//Labirinth Box+
			this->move(this->getDice(),true);
			break;
		case 8:	//Skull Box
			this->move(this->getNBox()-1,true);
			break;
		default:
			break;
	}
	cout <<"Press any key to continue . . .";getchar();
	if(curr!=this->position)
		this->action(m);	//iterate the action only if on a different box
}

void Player::handleCard(Carte c, Mazzo *m){
	string s="";
	switch(c.getId()){
		case 0:	//empty card
			break;
		case 1:	//move card
			this->move(1,false);	//move straight of 1 box
			break;
		case 2: //Blocked Card
			this->setTurn(1);	//block for 1 turn
			break;
		case 3: //Throw straight
			cout <<"Press enter to roll the dice . . .";
			getchar();
			this->setDice(this->dice());
			cout <<"WOW! hai tirato un bel " <<this->getDice()<<endl;
			this->move(this->getDice(),false);	//throw dice and move straight
			break;
		case 4: //throw back
			cout <<"Press enter to roll the dice . . .";
			getchar();
			this->setDice(this->dice());
			cout <<"WOW! You rolled a "<<this->getDice()<<endl;
			this->move(this->getDice(),true);	//throw dice and move backward
			break;
		case 5:	//back to start a player
			Player *app=this->next;
			if(app->getAge()==0)	app=app->next;	//skipping the sentinel
			if(app->getTurn()==0)	//moving player only if is unblocked
				app->move(app->getNBox()-1,true);		//next player goes to start box
			else cout<<app->getName() <<" is in jail. He can't be moved.";
			break;
	}
}
