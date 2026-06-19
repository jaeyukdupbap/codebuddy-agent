import json
import os
import logging
import urllib.request
import urllib.error
import ast
logger = logging.getLogger()
logger.setLevel(logging.INFO)


# =========================================================
# 공통 응답 빌더
# =========================================================
def build_success_response(event, response_body):
    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": event.get("actionGroup"),
            "apiPath": event.get("apiPath"),
            "httpMethod": event.get("httpMethod"),
            "httpStatusCode": 200,
            "responseBody": {
                "application/json": {
                    "body": json.dumps(response_body, ensure_ascii=False)
                }
            }
        }
    }


def build_error_response(event, error_msg, status_code):
    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": event.get("actionGroup"),
            "apiPath": event.get("apiPath"),
            "httpMethod": event.get("httpMethod"),
            "httpStatusCode": status_code,
            "responseBody": {
                "application/json": {
                    "body": json.dumps({"error": error_msg}, ensure_ascii=False)
                }
            }
        }
    }


def get_params(event):
    return {p["name"]: p["value"] for p in event.get("parameters", [])}


# =========================================================
# 1) GET /pr - PR 정보 조회 (기존 로직, 변경 없음)
# =========================================================
def handle_get_pr(event):
    params = get_params(event)
    owner = params.get("owner")
    repo_name = params.get("repo")
    pr_number = params.get("pr_number")

    logger.info(f"Fetching PR #{pr_number} from {owner}/{repo_name}")

    if not all([owner, repo_name, pr_number]):
        raise ValueError("Missing required parameters. Need owner, repo, pr_number")

    github_token = os.environ['GITHUB_TOKEN']
    url = f"https://api.github.com/repos/{owner}/{repo_name}/pulls/{pr_number}"
    req = urllib.request.Request(url)
    req.add_header('Authorization', f'token {github_token}')
    req.add_header('Accept', 'application/vnd.github.v3+json')
    req.add_header('User-Agent', 'CodeBuddy-Agent')

    with urllib.request.urlopen(req) as response:
        pr_data = json.loads(response.read().decode('utf-8'))

    response_body = {
        "title": pr_data.get("title", ""),
        "body": pr_data.get("body") or "",
        "state": pr_data.get("state", ""),
        "author": pr_data.get("user", {}).get("login", ""),
        "created_at": pr_data.get("created_at", ""),
        "updated_at": pr_data.get("updated_at", ""),
        "changed_files": pr_data.get("changed_files", 0),
        "additions": pr_data.get("additions", 0),
        "deletions": pr_data.get("deletions", 0),
        "diff_url": pr_data.get("diff_url", "")
    }
    logger.info(f"Successfully fetched PR #{pr_number}")
    return response_body


# =========================================================
# 2) POST /pr/comment - PR에 댓글 등록 (urllib로 재구현)
# =========================================================
def handle_post_comment(event):
    params = get_params(event)
    owner = params.get("owner")
    repo_name = params.get("repo")
    pr_number = params.get("pr_number")
    comment = params.get("comment")

    if not all([owner, repo_name, pr_number, comment]):
        raise ValueError("Missing required parameters. Need owner, repo, pr_number, comment")

    github_token = os.environ['GITHUB_TOKEN']
    url = f"https://api.github.com/repos/{owner}/{repo_name}/issues/{pr_number}/comments"

    payload = json.dumps({"body": comment}).encode('utf-8')
    req = urllib.request.Request(url, data=payload, method="POST")
    req.add_header('Authorization', f'token {github_token}')
    req.add_header('Accept', 'application/vnd.github.v3+json')
    req.add_header('User-Agent', 'CodeBuddy-Agent')
    req.add_header('Content-Type', 'application/json')

    with urllib.request.urlopen(req) as response:
        comment_data = json.loads(response.read().decode('utf-8'))

    logger.info(f"Comment added to PR #{pr_number}")
    return {
        "success": True,
        "message": f"Comment added to PR #{pr_number}",
        "comment_url": comment_data.get("html_url", "")
    }


# =========================================================
# 3) POST /complexity - 코드 복잡도 분석 (radon)
# =========================================================
def handle_analyze_complexity(event):
    from radon.complexity import cc_visit, cc_rank

    params = get_params(event)
    code = params.get("code", "")

    if not code:
        raise ValueError("Missing 'code' parameter")

    blocks = cc_visit(code)
    results = []
    high_complexity = []

    for block in blocks:
        complexity = block.complexity
        rank = cc_rank(complexity)
        item = {
            "name": block.name,
            "complexity": complexity,
            "rank": rank,
            "start_line": block.lineno,
            "end_line": block.endline
        }
        results.append(item)
        if complexity > 10:
            high_complexity.append(item)

    summary = {
        "total_functions": len(results),
        "average_complexity": (
            sum(c["complexity"] for c in results) / len(results) if results else 0
        ),
        "max_complexity": max((c["complexity"] for c in results), default=0),
        "high_complexity_count": len(high_complexity),
        "high_complexity_functions": high_complexity
    }

    return {"summary": summary, "details": results}


# =========================================================
# 4) POST /unittest - 단위 테스트 자동 생성 (Bedrock Claude 호출)
# =========================================================
def handle_generate_unit_test(event):
    import boto3

    params = get_params(event)
    code = params.get("code", "")
    function_name = params.get("function_name", "")

    if not code:
        raise ValueError("Missing 'code' parameter")

    bedrock = boto3.client('bedrock-runtime', region_name='ap-northeast-2')

    target_note = f"\n특히 '{function_name}' 함수에 집중해주세요." if function_name else ""

    prompt = f"""
당신은 테스트 엔지니어입니다. 다음 함수에 대한 pytest 단위 테스트 코드를 작성해주세요.

함수 코드:
```python
{code}
```
{target_note}

요구사항:
- 정상 입력 테스트
- 경계값 테스트 (0, None, 빈 리스트)
- 예외 상황 테스트
- pytest 스타일 사용

테스트 코드만 출력하세요 (설명 없이).
"""

    response = bedrock.converse(
        modelId='global.anthropic.claude-sonnet-4-6',
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"temperature": 0.2, "maxTokens": 2000}
    )

    test_code = response['output']['message']['content'][0]['text']
    return {"test_code": test_code}


# =========================================================
# 5) POST /refactor - 리팩토링 제안 (Bedrock Claude 호출)
# =========================================================
def handle_suggest_refactor(event):
    import boto3

    params = get_params(event)
    code = params.get("code", "")
    focus = params.get("focus", "maintainability")

    if not code:
        raise ValueError("Missing 'code' parameter")

    bedrock = boto3.client('bedrock-runtime', region_name='ap-northeast-2')

    prompt = f"""
당신은 시니어 개발자입니다. 다음 코드를 리팩토링하여 더 나은 구조를 제안해주세요.

코드:
```python
{code}
```

리팩토링 목표: {focus}

제안 형식:
1. 문제점 분석
2. 개선된 코드 (python 코드 블록)
3. 변경 이유 설명

개선된 코드는 실제 동작이 동일해야 합니다.
"""

    response = bedrock.converse(
        modelId='global.anthropic.claude-sonnet-4-6',
        messages=[{"role": "user", "content": [{"text": prompt}]}],
        inferenceConfig={"temperature": 0.3, "maxTokens": 3000}
    )

    suggestion = response['output']['message']['content'][0]['text']
    return {"suggestion": suggestion}


# =========================================================
# 6) POST /slack - Slack 알림 전송
# =========================================================
def handle_send_slack(event):
    params = get_params(event)
    message_text = params.get("message", "")
    status = params.get("status", "info")

    if not message_text:
        raise ValueError("Missing 'message' parameter")

    webhook_url = os.environ.get('SLACK_WEBHOOK_URL', '')
    if not webhook_url:
        logger.warning("SLACK_WEBHOOK_URL not set, skipping Slack notification")
        return {"success": False, "message": "Slack webhook not configured"}

    icon = {"success": "✅", "error": "❌", "info": "🔔"}.get(status, "🔔")
    payload = json.dumps({
        "text": f"{icon} *CodeBuddy 알림*\n{message_text}"
    }).encode('utf-8')

    req = urllib.request.Request(webhook_url, data=payload, method="POST")
    req.add_header('Content-Type', 'application/json')

    with urllib.request.urlopen(req) as response:
        response.read()

    logger.info("Slack notification sent")
    return {"success": True, "message": "Slack notification sent"}


# =========================================================
# 메인 핸들러: apiPath 라우팅
# =========================================================
ROUTES = {
    "/pr": handle_get_pr,
    "/pr/comment": handle_post_comment,
    "/complexity": handle_analyze_complexity,
    "/unittest": handle_generate_unit_test,
    "/refactor": handle_suggest_refactor,
    "/slack": handle_send_slack,
}


def handler(event, context):
    api_path = event.get("apiPath", "")
    logger.info(f"Routing apiPath: {api_path}")

    handler_fn = ROUTES.get(api_path)

    if handler_fn is None:
        return build_error_response(event, f"Unknown apiPath: {api_path}", 404)

    try:
        response_body = handler_fn(event)
        return build_success_response(event, response_body)

    except urllib.error.HTTPError as e:
        error_msg = f"GitHub API error: {e.code} {e.reason}"
        logger.error(error_msg)
        return build_error_response(event, error_msg, e.code if e.code else 500)

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return build_error_response(event, str(e), 400)

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return build_error_response(event, str(e), 500)
