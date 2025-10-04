import pytest
from unittest.mock import patch, MagicMock
from src.llm.groq_client import GroqClient

@pytest.fixture
def mock_groq_client():
    """Fixture to mock the Groq API client."""
    with patch('src.llm.groq_client.Groq') as mock_groq:
        mock_instance = MagicMock()
        mock_groq.return_value = mock_instance
        yield mock_instance

def test_groq_client_answer_generation(mock_groq_client):
    """
    Tests that the GroqClient correctly formats the prompt and returns the response.
    """
    # Mock the API response
    mock_response = MagicMock()
    mock_response.choices[0].message.content = "This is a test answer."
    mock_groq_client.chat.completions.create.return_value = mock_response

    client = GroqClient()
    question = "What is testing?"
    contexts = ["Context 1", "Context 2"]
    
    answer = client.answer(question, contexts)

    # Verify the prompt structure
    mock_groq_client.chat.completions.create.assert_called_once()
    call_args = mock_groq_client.chat.completions.create.call_args
    messages = call_args.kwargs['messages']
    
    assert messages[0]['role'] == 'system'
    assert "strictly using the provided sources" in messages[0]['content']
    assert messages[1]['role'] == 'user'
    assert "Question:\nWhat is testing?" in messages[1]['content']
    assert "[Source 1]\nContext 1" in messages[1]['content']
    assert "[Source 2]\nContext 2" in messages[1]['content']

    # Verify the answer
    assert answer == "This is a test answer."

def test_groq_client_no_context(mock_groq_client):
    """
    Tests that the client returns a specific message when no context is provided.
    """
    client = GroqClient()
    answer = client.answer("Any question", [])
    
    assert answer == "No sufficient context found."
    mock_groq_client.chat.completions.create.assert_not_called()
