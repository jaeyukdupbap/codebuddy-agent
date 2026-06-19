import boto3
import time
from dotenv import load_dotenv
import os

load_dotenv()

region = "ap-northeast-2"
agent_id = os.getenv("AGENT_ID")
alias_id = os.getenv("ALIAS_ID", "TSTALIASID")

bedrock_agent_runtime = boto3.client('bedrock-agent-runtime', region_name=region)

timestamp = int(time.time())


def invoke_agent(prompt, session_id):
    response = bedrock_agent_runtime.invoke_agent(
        agentId=agent_id,
        agentAliasId=alias_id,
        sessionId=session_id,
        inputText=prompt,
        enableTrace=True
    )

    full_response = ""
    for event in response['completion']:
        if 'chunk' in event:
            full_response += event['chunk']['bytes'].decode('utf-8')
        elif 'trace' in event:
            trace_info = event['trace']['trace']
            if 'orchestrationTrace' in trace_info:
                orch = trace_info['orchestrationTrace']
                if 'invocationInput' in orch:
                    print(f"\n🔧 Tool 호출 감지: {orch['invocationInput']}")
                elif 'observation' in orch:
                    print(f"\n💡 Agent Observation: {orch['observation']}")
                elif 'modelThought' in orch:
                    print(f"\n🤔 Agent Thought: {orch['modelThought']}")
    return full_response


test_code = '''
def process_data(items):
    result = []
    for item in items:
        if item > 0:
            if item % 2 == 0:
                result.append(item * 2)
            else:
                result.append(item * 3)
        else:
            result.append(0)
    return result
'''

print("=" * 60)
print("=== 테스트 1: analyze_complexity ===")
print("=" * 60)
result1 = invoke_agent(
    f"다음 코드의 순환 복잡도를 analyze_complexity 도구로 분석해줘:\n\n```python\n{test_code}\n```",
    session_id=f"test-complexity-{timestamp}"
)
print("\n🤖 Agent 응답 (복잡도 분석):")
print(result1)

print("\n" + "=" * 60)
print("=== 테스트 2: generate_unit_test ===")
print("=" * 60)
result2 = invoke_agent(
    f"다음 함수에 대한 pytest 단위 테스트를 generate_unit_test 도구로 만들어줘:\n\n```python\n{test_code}\n```",
    session_id=f"test-unittest-{timestamp}"
)
print("\n🤖 Agent 응답 (테스트 생성):")
print(result2)

print("\n" + "=" * 60)
print("=== 테스트 3: suggest_refactor ===")
print("=" * 60)
result3 = invoke_agent(
    f"다음 코드를 readability 관점에서 suggest_refactor 도구로 리팩토링 제안해줘:\n\n```python\n{test_code}\n```",
    session_id=f"test-refactor-{timestamp}"
)
print("\n🤖 Agent 응답 (리팩토링 제안):")
print(result3)
