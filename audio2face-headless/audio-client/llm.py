from openai import OpenAI

client = OpenAI()

voice = 'alloy'
text = '''
Widely regarded as one of the greatest films of all time, this mob drama, based on Mario Puzo's novel of the same name, focuses on the powerful Italian-American crime family of Don Vito Corleone (Marlon Brando). When the don's youngest son, Michael (Al Pacino), reluctantly joins the Mafia, he becomes involved in the inevitable cycle of violence and betrayal. Although Michael tries to maintain a normal relationship with his wife, Kay (Diane Keaton), he is drawn deeper into the family business.
'''

response = client.audio.speech.create(
    model="tts-1",
    voice=voice,
    input=text,
)

response.stream_to_file(f"{voice}-output.mp3")
