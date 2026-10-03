"""
Tests for AI Mock Interview APIs and Ollama integration evaluation.
"""

from unittest.mock import AsyncMock, patch
import pytest
from httpx import AsyncClient

from app.models.user import User


@pytest.fixture(autouse=True)
def mock_ollama_provider():
    """Autouse fixture to prevent real Ollama network timeouts during tests unless explicitly overridden."""
    with patch("app.integrations.ai.ollama.OllamaProvider.generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.side_effect = ConnectionError("Ollama offline in test sandbox")
        yield mock_gen


@pytest.mark.asyncio
async def test_create_interview_session(client: AsyncClient, auth_headers: dict[str, str]):
    """Test starting a new mock interview session."""
    payload = {
        "role": "Software Engineer",
        "difficulty": "Medium",
        "total_questions": 3,
    }

    res = await client.post("/api/v1/interviews", json=payload, headers=auth_headers)
    assert res.status_code == 201
    data = res.json()["data"]

    assert data["role"] == "Software Engineer"
    assert data["difficulty"] == "Medium"
    assert data["status"] == "in_progress"
    assert data["total_questions"] == 3
    assert data["current_question_index"] == 0
    assert data["current_question"] is not None
    assert len(data["questions"]) == 3




@pytest.mark.asyncio
async def test_list_user_interviews(client: AsyncClient, auth_headers: dict[str, str]):
    """Test listing user interview sessions history."""
    # Create 2 sessions
    await client.post(
        "/api/v1/interviews",
        json={"role": "Backend Engineer", "difficulty": "Easy", "total_questions": 2},
        headers=auth_headers,
    )
    await client.post(
        "/api/v1/interviews",
        json={"role": "Data Scientist", "difficulty": "Hard", "total_questions": 2},
        headers=auth_headers,
    )

    res = await client.get("/api/v1/interviews", headers=auth_headers)
    assert res.status_code == 200
    sessions = res.json()["data"]
    assert len(sessions) >= 2


@pytest.mark.asyncio
async def test_get_interview_session_by_id(client: AsyncClient, auth_headers: dict[str, str]):
    """Test retrieving session state by ID (safe for browser refresh)."""
    create_res = await client.post(
        "/api/v1/interviews",
        json={"role": "Full Stack Engineer", "difficulty": "Medium", "total_questions": 2},
        headers=auth_headers,
    )
    session_id = create_res.json()["data"]["id"]

    res = await client.get(f"/api/v1/interviews/{session_id}", headers=auth_headers)
    assert res.status_code == 200
    data = res.json()["data"]
    assert data["id"] == session_id
    assert data["role"] == "Full Stack Engineer"


@pytest.mark.asyncio
async def test_submit_answer_and_evaluate_with_ollama(client: AsyncClient, auth_headers: dict[str, str]):
    """Test submitting answer and obtaining 6-metric evaluation via mocked Ollama response."""
    create_res = await client.post(
        "/api/v1/interviews",
        json={"role": "Software Engineer", "difficulty": "Easy", "total_questions": 1},
        headers=auth_headers,
    )
    session_data = create_res.json()["data"]
    session_id = session_data["id"]
    active_q_id = session_data["current_question"]["id"]

    mock_eval_json = """
    {
      "technical_correctness": 88.0,
      "relevance": 92.0,
      "completeness": 85.0,
      "communication": 90.0,
      "structure": 86.0,
      "clarity": 94.0,
      "overall_score": 89.2,
      "feedback": "Great explanation of processes vs threads with clear examples.",
      "strengths": ["Clear technical concepts", "Good communication tone"],
      "improvements": ["Elaborate on memory isolation details"],
      "ideal_answer": "A process has isolated memory; a thread shares memory space."
    }
    """

    with patch("app.integrations.ai.ollama.OllamaProvider.generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_eval_json

        answer_payload = {
            "question_id": active_q_id,
            "user_answer": "A process is an isolated execution environment with its own virtual memory space. A thread is a lightweight thread of execution inside a process that shares memory with sibling threads.",
        }

        res = await client.post(
            f"/api/v1/interviews/{session_id}/answer",
            json=answer_payload,
            headers=auth_headers,
        )
        assert res.status_code == 200
        updated_session = res.json()["data"]
        assert updated_session["status"] == "completed"
        assert updated_session["overall_score"] == 89.2


@pytest.mark.asyncio
async def test_get_interview_results(client: AsyncClient, auth_headers: dict[str, str]):
    """Test retrieving final interview performance report."""
    create_res = await client.post(
        "/api/v1/interviews",
        json={"role": "DevOps Engineer", "difficulty": "Medium", "total_questions": 1},
        headers=auth_headers,
    )
    session_data = create_res.json()["data"]
    session_id = session_data["id"]
    active_q_id = session_data["current_question"]["id"]

    mock_eval_json = """
    {
      "technical_correctness": 90.0,
      "relevance": 90.0,
      "completeness": 90.0,
      "communication": 90.0,
      "structure": 90.0,
      "clarity": 90.0,
      "overall_score": 90.0,
      "feedback": "Excellent response.",
      "strengths": ["Deep knowledge"],
      "improvements": ["None"],
      "ideal_answer": "Ideal sample answer."
    }
    """

    with patch("app.integrations.ai.ollama.OllamaProvider.generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.return_value = mock_eval_json
        await client.post(
            f"/api/v1/interviews/{session_id}/answer",
            json={"question_id": active_q_id, "user_answer": "Detailed answer for DevOps role."},
            headers=auth_headers,
        )

    res = await client.get(f"/api/v1/interviews/{session_id}/results", headers=auth_headers)
    assert res.status_code == 200
    results = res.json()["data"]

    assert results["session_id"] == session_id
    assert results["role"] == "DevOps Engineer"
    assert "metrics_breakdown" in results
    assert results["metrics_breakdown"]["Technical Correctness"] == 90.0
    assert len(results["questions_transcript"]) == 1


@pytest.mark.asyncio
async def test_ollama_failure_handling(client: AsyncClient, auth_headers: dict[str, str]):
    """Test that Ollama connection failure returns 503 and does not complete evaluation falsely."""
    create_res = await client.post(
        "/api/v1/interviews",
        json={"role": "Cloud Architect", "difficulty": "Hard", "total_questions": 1},
        headers=auth_headers,
    )
    session_data = create_res.json()["data"]
    session_id = session_data["id"]
    active_q_id = session_data["current_question"]["id"]

    with patch("app.integrations.ai.ollama.OllamaProvider.generate", new_callable=AsyncMock) as mock_gen:
        mock_gen.side_effect = ConnectionError("Ollama host offline")

        res = await client.post(
            f"/api/v1/interviews/{session_id}/answer",
            json={"question_id": active_q_id, "user_answer": "Some candidate response."},
            headers=auth_headers,
        )
        assert res.status_code == 503
        assert "Ollama" in res.json()["message"]

    # Verify session remains in_progress and not falsely marked completed
    check_res = await client.get(f"/api/v1/interviews/{session_id}", headers=auth_headers)
    assert check_res.json()["data"]["status"] == "in_progress"
