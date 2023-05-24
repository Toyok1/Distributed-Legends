import concurrent
import grpc
import matchmaker_pb2
import matchmaker_pb2_grpc

import json

import game
import matchmaker_db



def trim_address(str):
  for i in range(len(str)):
    if str[i] == ':':
      address = str[i + 1:]
      break
  for i in range(len(address) - 1, -1, -1):
    if address[i] == ':':
      address = address[:i]
      break
  return address



class Matchmaker(matchmaker_pb2_grpc.MatchmakerServicer):

  def __init__(self):
    print('Matchmaker listening on port 900')

  def newGame(self, request, context):
    print(' => newGame\naddress: {:s}\ngame_id: {:s}\nplayer_id: {:s}'.format(trim_address(context.peer()), request.gameId, request.playerId))
    result = matchmakerDb.newGame(game.Game(trim_address(context.peer()), request.gameId, request.playerId))
    return matchmaker_pb2.NewGameReply(success = result)

  def listGame(self, request, context):
    print(' => listGame')
    for game in matchmakerDb.listGame():
      yield game.to_ListGameReply()

  def findGame(self, request, context):
    print(' => findGame\ngame_id: {:s}\nplayer_id: {:s}'.format(request.gameId, request.playerId))
    for game in matchmakerDb.findGame(request.gameId, request.playerId):
      yield game.to_FindGameReply()

  def deleteGame(self, request, context):
    print(' => deleteGame\naddress: {:s}\ngame_id: {:s}\nplayer_id: {:s}'.format(trim_address(context.peer()), request.gameId, request.playerId))
    result = matchmakerDb.deleteGame(trim_address(context.peer()), request.gameId, request.playerId)
    return matchmaker_pb2.DeleteGameReply(success = result)

  def listPlayer(self, request, context):
    print(' => listPlayer')
    for player in matchmakerDb.listPlayer(request.gameId, request.playerId):
      yield game.to_ListPlayerReply()



matchmakerDb = matchmaker_db.MatchmakerDb()



try:
  f = open('matchmaker_db.json', 'r')
  for g in json.loads(f.read()):
    matchmakerDb.newGame(game.Game(g['address'], g['game_id'], g['player_id']))
  f.close()
except Exception:
  pass



if __name__ == '__main__':
  server = grpc.server(concurrent.futures.ThreadPoolExecutor(max_workers = 10))
  matchmaker_pb2_grpc.add_MatchmakerServicer_to_server(Matchmaker(), server)
  server.add_insecure_port('[::]:900')
  server.start()
  server.wait_for_termination()
