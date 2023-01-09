#include <iostream>
#include <memory>
#include <string>

#include <grpcpp/grpcpp.h>

using grpc::Channel;
using grpc::ClientContext;
using grpc::Status;
using chat::ChatService;
using chat::ConnectRequest;
using chat::ConnectResponse;
using chat::DisconnectRequest;
using chat::DisconnectResponse;
using chat::SendMessageRequest;
using chat::SendMessageResponse;

class ChatClient {
 public:
  ChatClient(std::shared_ptr<Channel> channel)
      : stub_(ChatService::NewStub(channel)) {}

  // Connect to the server
  std::string Connect(const std::string& name) {
    ConnectRequest request;
    request.set_name(name);
    ConnectResponse response;
    ClientContext context;
    Status status = stub_->Connect(&context, request, &response);
    if (status.ok()) {
      return response.message();
    } else {
      return "Error connecting to server";
    }
  }

  // Disconnect from the server
  std::string Disconnect(const std::string& name) {
    DisconnectRequest request;
    request.set_name(name);
    DisconnectResponse response;
    ClientContext context;
    Status status = stub_->Disconnect(&context, request, &response);
    if (status.ok()) {
      return response.message();
    } else {
      return "Error disconnecting from server";
    }
  }

  // Send a message to all connected clients
  void SendMessage(const std::string& name, const std::string& message) {
    ClientContext context;
    std::unique_ptr<grpc::ClientReaderWriter<SendMessageRequest, SendMessageResponse>> stream(
        stub_->SendMessage(&context));

    // Send the request
    SendMessageRequest request;
    request.set_name(name);
    request.set_message(message);
    if (!stream->Write(request)) {
      std::cout << "Error sending message" << std::endl;
      return;
    }
    stream->WritesDone();

    // Receive the response
    SendMessageResponse response;
    while (stream->Read(&response)) {
      std::cout << response.name() << ": " << response.message() << std::endl;
    }
    Status status = stream->Finish();
    if (!status.ok()) {
      std::cout << "Error sending message" << std::endl;
    }
  }

 private:
  std::unique_ptr<ChatService::Stub> stub_;
};

int main(int argc, char** argv) {
  // Set up the channel to the server
  std::string server_address("localhost:50051");
  ChatClient chat(grpc::CreateChannel(
      server_address, grpc::InsecureChannelCredentials()));

  // Connect to the server
  std::string name = "Alice";
  std::cout << chat.Connect(name) << std::endl;

  // Send a message
  std::string message = "Hello, world!";
  chat.SendMessage(name, message);

  // Disconnect from the server
  std::cout << chat.Disconnect(name) << std::endl;

  return 0;
}