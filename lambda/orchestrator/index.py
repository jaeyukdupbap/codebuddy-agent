import json
import boto3
import os
import logging
from botocore.config import Config

logger = logging.getLogger()
logger.setLevel(logging.INFO)

lambda_client = boto3.client('lambda', region_name='ap-northeast-2')

AGENT_ID = os.environ.get('AGENT_ID')
ALIAS_ID = os.environ.get('ALIAS_ID')
WORKER_FUNCTION = os.environ.get('WORKER_FUNCTION', 'codebuddy-worker')


def respond(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*"
        },
        "body": json.dumps(body, ensure_ascii=False)
    }


def parse_pr_url(pr_url):
    parts = pr_url.rstrip('/').split('/')
    if len(parts) < 4 or 'pull' not in parts:
        raise ValueError("Invalid PR URL format. Expected: https://github.com/owner/repo/pull/123")
    pr_number = int(parts[-1])
    repo = parts[-3]
    owner = parts[-4]
    return owner, repo, pr_number


def handler(event, context):
    logger.info(f"Received event: {json.dumps(event)}")

    # Worker Lambda가 직접 호출한 경우 (비동기 실행)
    if event.get('_async_worker'):
        return run_agent_review(event)

    # API Gateway에서 온 요청 처리
    try:
        body = json.loads(event.get('body') or '{}')
        pr_url = body.get('pr_url')
        action = body.get('action', 'review')

        if not pr_url:
            return respond(400, {"error": "Missing pr_url"})

        owner, repo, pr_number = parse_pr_url(pr_url)

        # 같은 Lambda를 비동기로 호출 (InvocationType=Event → 즉시 반환)
        lambda_client.invoke(
            FunctionName=context.function_name,
            InvocationType='Event',
            Payload=json.dumps({
                '_async_worker': True,
                'pr_url': pr_url,
                'owner': owner,
                'repo': repo,
                'pr_number': pr_number,
                'action': action
            })
        )

        logger.info(f"Async worker triggered for PR #{pr_number}")
        return respond(202, {
            "message": "리뷰 시작됨",
            "status": "processing",
            "pr_url": pr_url,
            "info": "분석 완료 후 PR에 댓글이 등록됩니다."
        })

    except ValueError as e:
        logger.error(f"Validation error: {e}")
        return respond(400, {"error": str(e)})

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return respond(500, {"error": str(e)})


def run_agent_review(event):
    bedrock_agent_runtime = boto3.client(
        'bedrock-agent-runtime',
        region_name='ap-northeast-2',
        config=Config(read_timeout=280, connect_timeout=10)
    )

    pr_url = event.get('pr_url')
    owner = event.get('owner')
    repo = event.get('repo')
    pr_number = event.get('pr_number')

    prompt = f"""다음 GitHub Pull Request를 종합적으로 분석해주세요:
저장소: {owner}/{repo}
PR 번호: {pr_number}

수행할 작업:
1. get_github_pr 도구로 PR 정보를 가져오세요.
2. PR의 코드에서 스타일 위반, 보안 취약점을 검토하세요.
3. analyze_complexity 도구로 복잡도가 높은 함수를 분석하세요.
4. 복잡도가 높은 함수가 있다면 suggest_refactor 도구로 리팩토링을 제안하세요.
5. generate_unit_test 도구로 필요한 테스트 코드를 생성하세요.
6. 위 모든 결과를 종합하여 post_pr_comment 도구로 PR에 댓글을 등록하세요.
7. 완료되면 send_slack_notification 도구로 팀에 알려주세요.
"""

    try:
        response = bedrock_agent_runtime.invoke_agent(
            agentId=AGENT_ID,
            agentAliasId=ALIAS_ID,
            sessionId=f"async-{owner}-{repo}-{pr_number}",
            inputText=prompt,
            enableTrace=False
        )

        result_text = ""
        for stream_event in response['completion']:
            if 'chunk' in stream_event:
                result_text += stream_event['chunk']['bytes'].decode('utf-8')

        logger.info(f"Async review completed for PR #{pr_number}")
        return {"status": "completed", "result": result_text[:500]}

    except Exception as e:
        logger.error(f"Async worker error: {str(e)}")
        return {"status": "error", "error": str(e)}
