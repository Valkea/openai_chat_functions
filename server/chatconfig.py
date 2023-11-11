
import os
import json
import smtplib
import ssl
from email.message import EmailMessage

import openai

from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())  # read local .env file
openai.api_key = os.getenv("OPENAI_API_KEY")


class ToolBot():

    def __init__(self, client):
        self.client = client
        self.model = "gpt-3.5-turbo-1106"
        self.history = [] # The history should be stored in a user session variable !
        self.tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_current_weather",
                    "description": "Get the current weather in a given location",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "location": {
                                "type": "string",
                                "description": "The city and state, e.g. San Francisco, CA",
                            },
                            "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                        },
                        "required": ["location"],
                    },
                },
            },
            {
                "type": "function",
                "function": {
                    "name": "send_email",
                    "description": "Send an email to a given recipient",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "email": {
                                "type": "string",
                                "description": "The address email that needs to be used as the receiver email address",
                            },
                            "subject": {
                                "type": "string",
                                "description": "The subject (i.e. the Overall idea) of the email",
                            },
                            "message": {
                                "type": "string",
                                "description": "The message to be sent to the recipient",
                            },

                            "unit": {"type": "string", "enum": ["celsius", "fahrenheit"]},
                        },
                        "required": ["email", "subject", "message"],
                    },
                },
            }
        ]

        self.available_functions = {
            "get_current_weather": self.get_current_weather,
            "send_email": self.send_email,
        }

    def send_query(self, query):

        if query is not None:
            message = {"role": "user", "content": query}
            self.history.append(message)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.history,
            tools=self.tools,
            tool_choice="auto",  # auto is default, but we'll be explicit
        )
        return self.parse_response(response)

    def parse_response(self, response):

        response_message = response.choices[0].message
        print("debug:", response_message)

        tool_calls = response_message.tool_calls
        if tool_calls:

            self.history.append(response_message)

            # Step 4: send the info for each function call and function response to the model
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_to_call = self.available_functions[function_name]
                function_args = json.loads(tool_call.function.arguments)
                print("function_to_call:", function_to_call.__name__)

                if function_to_call.__name__ == "send_email":
                    function_response = function_to_call(
                        email=function_args.get("email"),
                        subject=function_args.get("subject"),
                        message=function_args.get("message"),
                    )
                    re_query = True

                else:
                    function_response = function_to_call(
                        location=function_args.get("location"),
                        unit=function_args.get("unit"),
                    )
                    re_query = True

                message = {
                        "role": "tool",
                        "content": function_response,
                        "tool_call_id": tool_call.id,
                        "name": function_name,
                        }
                self.history.append(message)

                if re_query:
                    return self.send_query(None)
                else:
                    return function_response

        else:
            message = {
                "role": "assistant",
                "content": response_message.content,
                }
            self.history.append(message)
            return response_message.content


    # ===== TOOLS =====

    def send_email(self, email, subject, message):

        # Define email sender and receiver
        email_sender = os.getenv('EMAIL_ADDRESS')
        email_password = os.getenv('EMAIL_PASSWORD')
        email_smtp = os.getenv('EMAIL_SMTP')
        email_port = os.getenv('EMAIL_PORT')
        email_receiver = email

        # Set the email
        em = EmailMessage()
        em['From'] = email_sender
        em['To'] = email_receiver
        em['Subject'] = subject
        em.set_content(message)

        # Add SSL (layer of security)
        context = ssl.create_default_context()

        # Log in and send the email
        try:
            with smtplib.SMTP_SSL(email_smtp, email_port, context=context) as smtp:
                smtp.login(email_sender, email_password)
                smtp.sendmail(email_sender, email_receiver, em.as_string())

            return "email sent"
        except Exception:
            return "an error occured"

    # In production, this could be your backend API or an external API
    def get_current_weather(self, location, unit="fahrenheit"):
        """Get the current weather in a given location"""
        if "tokyo" in location.lower():
            return json.dumps({"location": "Tokyo", "temperature": "10", "unit": "celsius"})
        elif "san francisco" in location.lower():
            return json.dumps({"location": "San Francisco", "temperature": "72", "unit": "fahrenheit"})
        elif "paris" in location.lower():
            return json.dumps({"location": "Paris", "temperature": "22", "unit": "celsius"})
        else:
            return json.dumps({"location": location, "temperature": "unknown"})
