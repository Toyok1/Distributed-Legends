# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: chat.proto
"""Generated protocol buffer code."""
from google.protobuf.internal import builder as _builder
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\nchat.proto\x12\x04grpc\"\x07\n\x05\x45mpty\"%\n\x04Note\x12\x0c\n\x04name\x18\x01 \x01(\t\x12\x0f\n\x07message\x18\x02 \x01(\t\"\x1e\n\x0bStartedBool\x12\x0f\n\x07started\x18\x01 \x01(\x08\"H\n\x0bPrivateInfo\x12\n\n\x02ip\x18\x01 \x01(\x0c\x12\x0c\n\x04user\x18\x02 \x01(\t\x12\x0c\n\x04u_id\x18\x03 \x01(\t\x12\x11\n\tuser_type\x18\x04 \x01(\x05\"!\n\rPlayerMessage\x12\x10\n\x08json_str\x18\x01 \x01(\t\"\x1e\n\x04Ping\x12\n\n\x02ip\x18\x01 \x01(\x0c\x12\n\n\x02id\x18\x02 \x01(\t\"\x17\n\x04Pong\x12\x0f\n\x07message\x18\x01 \x01(\t\"L\n\nGameStatus\x12\x11\n\ttimeStamp\x18\x01 \x01(\t\x12\x17\n\x0fplayerPositions\x18\x02 \x01(\t\x12\x12\n\nlastPlayer\x18\x03 \x01(\t\"/\n\x0bInitialList\x12\x0e\n\x06length\x18\x01 \x01(\x05\x12\x10\n\x08json_str\x18\x02 \x01(\t\"&\n\x06Health\x12\x10\n\x08json_str\x18\x01 \x01(\t\x12\n\n\x02hp\x18\x02 \x01(\x05\"(\n\x05\x42lock\x12\x10\n\x08json_str\x18\x01 \x01(\t\x12\r\n\x05\x62lock\x18\x02 \x01(\x05\"O\n\x06\x41\x63tion\x12\x0e\n\x06sender\x18\x01 \x01(\t\x12\x10\n\x08reciever\x18\x02 \x01(\t\x12\x0e\n\x06\x61mount\x18\x03 \x01(\x05\x12\x13\n\x0b\x61\x63tion_type\x18\x04 \x01(\x05\x32\xcb\x05\n\nChatServer\x12\'\n\nChatStream\x12\x0b.grpc.Empty\x1a\n.grpc.Note0\x01\x12#\n\x08SendNote\x12\n.grpc.Note\x1a\x0b.grpc.Empty\x12\x31\n\x0fSendPrivateInfo\x12\x11.grpc.PrivateInfo\x1a\x0b.grpc.Empty\x12\"\n\x08SendPing\x12\n.grpc.Ping\x1a\n.grpc.Pong\x12\x31\n\tStartGame\x12\x11.grpc.PrivateInfo\x1a\x11.grpc.InitialList\x12\'\n\nSendHealth\x12\x0c.grpc.Health\x1a\x0b.grpc.Empty\x12%\n\tSendBlock\x12\x0b.grpc.Block\x1a\x0b.grpc.Empty\x12\'\n\nSendAction\x12\x0c.grpc.Action\x1a\x0b.grpc.Empty\x12+\n\x0cHealthStream\x12\x0b.grpc.Empty\x1a\x0c.grpc.Health0\x01\x12)\n\x0b\x42lockStream\x12\x0b.grpc.Empty\x1a\x0b.grpc.Block0\x01\x12+\n\x0c\x41\x63tionStream\x12\x0b.grpc.Empty\x1a\x0c.grpc.Action0\x01\x12\x30\n\x0eGetInitialList\x12\x0b.grpc.Empty\x1a\x11.grpc.InitialList\x12%\n\nFinishGame\x12\x0b.grpc.Empty\x1a\n.grpc.Note\x12+\n\x07\x45ndTurn\x12\x13.grpc.PlayerMessage\x1a\x0b.grpc.Empty\x12\x30\n\nTurnStream\x12\x0b.grpc.Empty\x1a\x13.grpc.PlayerMessage0\x01\x12/\n\rReturnStarted\x12\x0b.grpc.Empty\x1a\x11.grpc.StartedBoolb\x06proto3')

_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, globals())
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'chat_pb2', globals())
if _descriptor._USE_C_DESCRIPTORS == False:

  DESCRIPTOR._options = None
  _EMPTY._serialized_start=20
  _EMPTY._serialized_end=27
  _NOTE._serialized_start=29
  _NOTE._serialized_end=66
  _STARTEDBOOL._serialized_start=68
  _STARTEDBOOL._serialized_end=98
  _PRIVATEINFO._serialized_start=100
  _PRIVATEINFO._serialized_end=172
  _PLAYERMESSAGE._serialized_start=174
  _PLAYERMESSAGE._serialized_end=207
  _PING._serialized_start=209
  _PING._serialized_end=239
  _PONG._serialized_start=241
  _PONG._serialized_end=264
  _GAMESTATUS._serialized_start=266
  _GAMESTATUS._serialized_end=342
  _INITIALLIST._serialized_start=344
  _INITIALLIST._serialized_end=391
  _HEALTH._serialized_start=393
  _HEALTH._serialized_end=431
  _BLOCK._serialized_start=433
  _BLOCK._serialized_end=473
  _ACTION._serialized_start=475
  _ACTION._serialized_end=554
  _CHATSERVER._serialized_start=557
  _CHATSERVER._serialized_end=1272
# @@protoc_insertion_point(module_scope)
