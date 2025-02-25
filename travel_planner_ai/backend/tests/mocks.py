from unittest.mock import MagicMock

class MockAsyncOpenAI:
    def __init__(self, *args, **kwargs):
        self.chat = MagicMock()
        self.chat.completions = MagicMock()
        self.chat.completions.create = MagicMock()

class MockResponse:
    def __init__(self, content):
        self.choices = [MagicMock(message=MagicMock(content=content))]

def mock_openai_response():
    return MockResponse('{"days": []}') 