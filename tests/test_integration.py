import requests
import json

def test_asr_got_query():
    """
    Test a basic query to the ASR-GoT MCP server.
    """
    url = "http://localhost:8082/api/v1/query"
    
    payload = {
        "query": "Investigate the role of skin microbiome in cutaneous T-cell lymphoma progression.",
        "context": {},
        "parameters": {
            "evidence_max_iterations": 3
        }
    }
    
    response = requests.post(url, json=payload)
    assert response.status_code == 200
    
    result = response.json()
    print(json.dumps(result, indent=2))
    
    # Verify basic structure
    assert "result" in result
    assert "reasoning_trace" in result
    assert "graph_state" in result
    
    # Get graph state for visualization
    session_id = result.get("result", {}).get("session_id")
    if session_id:
        graph_url = f"http://localhost:8082/api/v1/graph/{session_id}"
        graph_response = requests.get(graph_url)
        assert graph_response.status_code == 200
        
        print("\nGraph State:")
        print(json.dumps(graph_response.json(), indent=2))

def test_claude_integration():
    """
    Test Claude integration with ASR-GoT.
    """
    url = "http://localhost:8082/api/v1/claude/query"
    
    payload = {
        "query": "Analyze the relationship between chromosomal instability and treatment resistance in cutaneous malignancies.",
        "process_response": True
    }
    
    response = requests.post(url, json=payload)
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        return
    
    result = response.json()
    
    # Print Claude's response
    print("Claude's Response:")
    choices = result.get("choices", [])
    if choices:
        content = choices[0].get("message", {}).get("content", "")
        print(content[:500] + "...\n")
    
    # Print ASR-GoT processing results if available
    asr_got_result = result.get("asr_got_result")
    if asr_got_result:
        print("ASR-GoT Processing Results:")
        print(json.dumps(asr_got_result, indent=2))

if __name__ == "__main__":
    print("Testing ASR-GoT Query...")
    test_asr_got_query()
    
    print("\n" + "="*50 + "\n")
    
    print("Testing Claude Integration...")
    test_claude_integration()