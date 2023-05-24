import matchmaker_pb2



class Game:

  def __init__(self, address, game_id, player_id):
    self.address = address
    self.game_id = game_id
    self.player_id = player_id
    self.list_client = []

  def to_ListGameReply(self):
    return matchmaker_pb2.ListGameReply(address = self.address, gameId = self.game_id, playerId = self.player_id)
  
  def to_FindGameReply(self):
    return matchmaker_pb2.ListGameReply(address = self.address, gameId = self.game_id, playerId = self.player_id)

  def add_to_list_client(self,address, player_id):
    self.list_client.append([address, player_id])
  
  def remove(self,address, player_id):
    self.list_client.remove([address, player_id])

  def to_ListPlayerReply(self):
    return matchmaker_pb2.ListPlayerReply(address = self.address, gameId = self.game_id)
  
  def to_dict(self):
    return {
      'address': self.address,
      'game_id': self.game_id,
      'player_id': self.player_id,
      'list_client': self.list_client
    }
