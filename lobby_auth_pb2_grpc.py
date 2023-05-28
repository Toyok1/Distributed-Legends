# Generated by the gRPC Python protocol compiler plugin. DO NOT EDIT!
"""Client and server classes corresponding to protobuf-defined services."""
import grpc

import lobby_auth_pb2 as lobby__auth__pb2


class LobbyAuthServerStub(object):
    """Missing associated documentation comment in .proto file."""

    def __init__(self, channel):
        """Constructor.

        Args:
            channel: A grpc.Channel.
        """
        self.SendPrivateInfo = channel.unary_unary(
                '/grpc.LobbyAuthServer/SendPrivateInfo',
                request_serializer=lobby__auth__pb2.PrivateInfo.SerializeToString,
                response_deserializer=lobby__auth__pb2.PlayersList.FromString,
                )
        self.StartGame = channel.unary_unary(
                '/grpc.LobbyAuthServer/StartGame',
                request_serializer=lobby__auth__pb2.PrivateInfo.SerializeToString,
                response_deserializer=lobby__auth__pb2.Empty_Lobby.FromString,
                )
        self.GetPlayerList = channel.unary_unary(
                '/grpc.LobbyAuthServer/GetPlayerList',
                request_serializer=lobby__auth__pb2.PrivateInfo.SerializeToString,
                response_deserializer=lobby__auth__pb2.PlayersList.FromString,
                )


class LobbyAuthServerServicer(object):
    """Missing associated documentation comment in .proto file."""

    def SendPrivateInfo(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def StartGame(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')

    def GetPlayerList(self, request, context):
        """Missing associated documentation comment in .proto file."""
        context.set_code(grpc.StatusCode.UNIMPLEMENTED)
        context.set_details('Method not implemented!')
        raise NotImplementedError('Method not implemented!')


def add_LobbyAuthServerServicer_to_server(servicer, server):
    rpc_method_handlers = {
            'SendPrivateInfo': grpc.unary_unary_rpc_method_handler(
                    servicer.SendPrivateInfo,
                    request_deserializer=lobby__auth__pb2.PrivateInfo.FromString,
                    response_serializer=lobby__auth__pb2.PlayersList.SerializeToString,
            ),
            'StartGame': grpc.unary_unary_rpc_method_handler(
                    servicer.StartGame,
                    request_deserializer=lobby__auth__pb2.PrivateInfo.FromString,
                    response_serializer=lobby__auth__pb2.Empty_Lobby.SerializeToString,
            ),
            'GetPlayerList': grpc.unary_unary_rpc_method_handler(
                    servicer.GetPlayerList,
                    request_deserializer=lobby__auth__pb2.PrivateInfo.FromString,
                    response_serializer=lobby__auth__pb2.PlayersList.SerializeToString,
            ),
    }
    generic_handler = grpc.method_handlers_generic_handler(
            'grpc.LobbyAuthServer', rpc_method_handlers)
    server.add_generic_rpc_handlers((generic_handler,))


 # This class is part of an EXPERIMENTAL API.
class LobbyAuthServer(object):
    """Missing associated documentation comment in .proto file."""

    @staticmethod
    def SendPrivateInfo(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/grpc.LobbyAuthServer/SendPrivateInfo',
            lobby__auth__pb2.PrivateInfo.SerializeToString,
            lobby__auth__pb2.PlayersList.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def StartGame(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/grpc.LobbyAuthServer/StartGame',
            lobby__auth__pb2.PrivateInfo.SerializeToString,
            lobby__auth__pb2.Empty_Lobby.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)

    @staticmethod
    def GetPlayerList(request,
            target,
            options=(),
            channel_credentials=None,
            call_credentials=None,
            insecure=False,
            compression=None,
            wait_for_ready=None,
            timeout=None,
            metadata=None):
        return grpc.experimental.unary_unary(request, target, '/grpc.LobbyAuthServer/GetPlayerList',
            lobby__auth__pb2.PrivateInfo.SerializeToString,
            lobby__auth__pb2.PlayersList.FromString,
            options, channel_credentials,
            insecure, call_credentials, compression, wait_for_ready, timeout, metadata)
