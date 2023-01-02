output: main.cpp menu.o game.o Card.o CardDeck.o player.o box.o map.o
	g++ main.cpp menu.o game.o Card.o CardDeck.o player.o box.o map.o -o ../GOP
	rm *.o *.h.gch
	@echo Main - Done
	@echo Everything Done!

box.o: box.cpp box.h
	g++ -c box.cpp box.h
	@echo Box - done

map.o: map.cpp map.h box.h
	g++ -c map.cpp map.h box.h
	@echo Map - done

game.o: game.cpp game.h menu.h CardDeck.h player.h map.h
	g++ -c game.cpp game.h menu.h CardDeck.h player.h map.h
	@echo GAME - Done

CardDeck.o: CardDeck.cpp CardDeck.h Card.h
	g++ -c CardDeck.cpp CardDeck.h Card.h
	@echo CardDeck - done

Card.o: Card.cpp Card.h
	g++ -c Card.cpp Card.h
	@echo CARTE - done

player.o: player.cpp player.h
	g++ -c player.cpp player.h
	@echo PLAYER - done

menu.o: menu.cpp menu.h 
	g++ -c menu.cpp menu.h 
	@echo Menu - done

clean:
	rm ../GOP
	@echo Removed All!
