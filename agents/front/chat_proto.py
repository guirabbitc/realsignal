"""The front agent's Chat Protocol: every message goes to the conversation in flow.py."""
from chat import make_chat_protocol
from front.flow import handle_founder_input

chat_proto = make_chat_protocol(handle_founder_input)
