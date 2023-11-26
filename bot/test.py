from telethon.sync import TelegramClient, events, functions

# Replace these values with your own
api_id = '13031929'
api_hash = '1a3e676f744e9e6145024e232b079bc4'

# Replace 'your_phone_number' with your actual phone number, including the country code
phone_number = '+380935358497'

# Create a session file to store the session information
session_file = 'session_name'
bot_token = '5323882359:AAFIUxLGcdgiEzEsYShmI6CwI9FvX1oKZOc'
# Connect to the Telegram API
client = TelegramClient(session_file, api_id, api_hash).start(bot_token=bot_token)

@client.on(events.NewMessage)
async def echo(event: events.NewMessage.Event):
  
    print(f"Received message: {event.message.message}")
    # Send the same message back
    await client.send_message('m1i1ha', event.message.message, formatting_entities = event.message.entities)

async def main():
    # Ensure you're authorized
    await client.connect()

    if not await client.is_user_authorized():
        await client.send_code_request(phone_number)
        await client.sign_in(phone_number, input('Enter the code: '))

    # Start listening for incoming messages
    await client.run_until_disconnected()

# Run the script
with client:
    client.loop.run_until_complete(main())