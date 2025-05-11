import re


class Ollama:
    def __init__(self, host: str = "http://localhost:11434"):
        self.host = host
        import requests

        self.requests = requests

    def generate(self, model, prompt, stream=False):
        """
        Generates text based on a given prompt using the specified model.

        Args:
            model (str): The name of the Ollama model to use.
            prompt (str): The input prompt for text generation.
            stream (bool): whether to stream the response

        Returns:
            str: The generated text.
        """
        url = f"{self.host}/api/generate"
        data = {"model": model, "prompt": prompt, "stream": stream}
        try:
            response = self.requests.post(url, json=data, stream=stream)
            response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
            if stream:
                full_response = ""
                for chunk in response.iter_lines():
                    if chunk:
                        import json

                        decoded_chunk = json.loads(chunk.decode("utf-8"))
                        full_response += decoded_chunk.get("response", "")
                        if decoded_chunk.get("done"):
                            break
                return full_response
            else:
                r = response.json()["response"]
                # Extract the thinking and response parts
                match = re.search(r"<think>(.*?)</think>\s*(.*)", r, re.DOTALL)

                d = {"thinking": [], "response": ""}

                if match:
                    thinking_text = match.group(1).strip()
                    response_text = match.group(2).strip()
                    d["thinking"] = [
                        line.strip()
                        for line in thinking_text.splitlines()
                        if line.strip()
                    ]
                    d["response"] = response_text
                else:
                    d["response"] = r
                return d
        except self.requests.exceptions.RequestException as e:
            raise Exception(f"Error during Ollama API request: {e}")
