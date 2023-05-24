import grpc
import matchmaker_pb2
import matchmaker_pb2_grpc

import json



if __name__ == '__main__':
  f = open('matchmaker_address.json', 'r')
  matchmaker_address = json.loads(f.read())['matchmakerAddress']
  f.close()
  
  matchmaker_address_manual = str(input('Matchmaker address (default: {:s}): '.format(matchmaker_address)))
  if matchmaker_address_manual and matchmaker_address_manual != matchmaker_address:
    matchmaker_address = matchmaker_address_manual
  
  print('connecting to {:s}'.format(matchmaker_address))
  channel = grpc.insecure_channel('{:s}:900'.format(matchmaker_address))
  stub = matchmaker_pb2_grpc.MatchmakerStub(channel)

  command = input(' > ')
  while command != 'exit':
    if command == 'new-game':
      print('==============================')
      game_id = str(input('Game id: '))
      player_id = str(input('Player id: '))
      response = stub.newGame(matchmaker_pb2.NewGameRequest(gameId = game_id, playerId = player_id))
      print('{:s}'.format('DONE' if response.success else 'ERROR'))
      print('==============================')
    elif command == 'list-game':
      response_stream = stub.listGame(matchmaker_pb2.ListGameRequest())
      for game in response_stream:
        print('==============================')
        print(game)
      print('==============================')
    elif command == 'find-game':
      print('==============================')
      game_id = str(input('Game id: '))
      player_id = str(input('Player id: '))
      response_stream = stub.findGame(matchmaker_pb2.FindGameRequest(gameId = game_id, playerId = player_id))
      for game in response_stream:
        print('==============================')
        print(game)
      print('==============================')
    elif command == 'delete-game':
      print('==============================')
      game_id = str(input('Game id: '))
      player_id = str(input('Player id: '))
      response = stub.deleteGame(matchmaker_pb2.DeleteGameRequest(gameId = game_id, playerId = player_id))
      print('{:s}'.format('DONE' if response.success else 'ERROR'))
      print('==============================')
    elif command == 'list-players':
      print('==============================')
      game_id = str(input('Game id: '))
      response = stub.listPlayers(matchmaker_pb2.ListPlayerRequest(gameId = game_id))
      for player in response:
        print('==============================')
        print(player)
      
    command = input(' > ')
