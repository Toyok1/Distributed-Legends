import json

import game



class MatchmakerDb:

  def __init__(self):
    self.game_list = list()
    # TODODSE
    # Solo per avere su cosa provare
    self.game_list = [game.Game('0.0.0.0', '[do not use]test_1', 'player_1', ['mario','luigi']), game.Game('0.0.0.0', '[do not use]test_2', 'player_2'), game.Game('0.0.0.0', '[do not use]test_3', 'player_3')]

  def newGame(self, game):
    game_list = list(filter(lambda x: x.player_id == game.player_id, filter(lambda x: x.game_id == game.game_id, filter(lambda x: x.address == game.address, self.game_list))))
    if len(game_list) == 0:
      self.game_list.append(game)
      return True
    else:
      return False

  def listGame(self):
    return self.game_list
  
  def findGame(self, game_id, player_id):
    game_list = self.game_list
    if game_id :
      game_list = list(filter(lambda x: x.game_id == game_id, game_list))
    if player_id:
      game_list = list(filter(lambda x: x.player_id == player_id, game_list))
    return game_list

  def deleteGame(self, address, game_id, player_id):
    game_list = list(filter(lambda x: x.player_id == player_id, filter(lambda x: x.game_id == game_id, filter(lambda x: x.address == address, self.game_list))))
    if len(game_list) == 1:
      self.game_list.remove(game_list[0])
      return True
    else:
      return False
    
  def listPlayer(self, game_id):
    gameSelector = self.game_list
    if game_id :
      gameSelector = list(filter(lambda x: x.game_id == game_id, gameSelector))
    return gameSelector[0].listPlayer()

  def saveGame(self):
    f = open('matchmaker_db.json', 'w')
    f.write(json.dumps([x.to_dict() for x in self.game_list], indent = 2))
    f.close()
    return True
