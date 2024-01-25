"""Test the token passing."""
from workflow.definitions.work import Work
from workflow.http.context import HTTPContext


def test_work_pass_token_to_client(monkeypatch):
    """Test that the Client objects can obtain token from Work object."""
    test_token = "ghp_1234567890abcdefg"
    monkeypatch.setenv("WORKFLOW_HTTP_TOKEN", test_token)
    http = HTTPContext(timeout=10)
    work = Work(pipeline="test", site="local", user="test", http=http)

    # ? Check HTTPContext have token
    assert http.token.get_secret_value() == test_token  # type: ignore

    # ? Check clients have token
    assert work.http.buckets.token.get_secret_value() == test_token  # type: ignore
    assert work.http.results.token.get_secret_value() == test_token  # type: ignore
    assert work.http.pipelines.token.get_secret_value() == test_token  # type: ignore
