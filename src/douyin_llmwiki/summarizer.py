from __future__ import annotations

import json
from typing import Any

from .errors import SummaryError
from .models import Summary, VideoMetadata
from .utils import split_text


class QwenSummarizer:
    def __init__(
        self,
        api_key: str,
        model: str,
        base_url: str,
        max_chunk_chars: int,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.max_chunk_chars = max_chunk_chars

    def summarize(self, transcript_text: str, metadata: VideoMetadata) -> Summary:
        chunks = split_text(transcript_text, self.max_chunk_chars)
        if len(chunks) == 1:
            return self._summarize_text(chunks[0], metadata, final=True)

        partials = [
            self._summarize_text(chunk, metadata, final=False, chunk_index=index + 1, chunk_total=len(chunks))
            for index, chunk in enumerate(chunks)
        ]
        merged_input = "\n\n".join(json.dumps(part.raw, ensure_ascii=False) for part in partials)
        return self._summarize_text(merged_input, metadata, final=True, from_partials=True)

    def _summarize_text(
        self,
        text: str,
        metadata: VideoMetadata,
        final: bool,
        chunk_index: int | None = None,
        chunk_total: int | None = None,
        from_partials: bool = False,
    ) -> Summary:
        requests = _requests()
        response = requests.post(
            f"{self.base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": self.model,
                "messages": self._messages(text, metadata, final, chunk_index, chunk_total, from_partials),
                "temperature": 0.2,
            },
            timeout=120,
        )
        if response.status_code >= 400:
            raise SummaryError(
                f"Summary model call failed: HTTP {response.status_code} {response.text}"
            )
        try:
            data = response.json()
        except ValueError as exc:
            raise SummaryError("Summary model response was not JSON.") from exc

        content = (
            data.get("choices", [{}])[0]
            .get("message", {})
            .get("content", "")
        )
        if not isinstance(content, str) or not content.strip():
            raise SummaryError(f"Summary model response did not include content: {data}")
        return parse_summary_json(content)

    def _messages(
        self,
        text: str,
        metadata: VideoMetadata,
        final: bool,
        chunk_index: int | None,
        chunk_total: int | None,
        from_partials: bool,
    ) -> list[dict[str, str]]:
        stage = "最终总结" if final else f"分段总结 {chunk_index}/{chunk_total}"
        source_kind = "多个分段总结 JSON" if from_partials else "ASR 转写文本"
        system = (
            "你是一个把视频音频转写整理成 Obsidian 本地知识库条目的中文知识萃取 agent。"
            "目标不是写普通摘要，而是把内容沉淀为可复用、可执行、可复习的知识资产。"
            "只输出一个合法 JSON 对象，不要输出 Markdown、代码块或额外解释。"
        )
        user = f"""
任务：{stage}
输入类型：{source_kind}
视频标题：{metadata.title}
发布者：{metadata.uploader or "未知"}
视频链接：{metadata.webpage_url or metadata.source_url}

请输出以下 JSON 字段，字段名必须完全一致：
{{
  "knowledge_title": "给这条视频沉淀出的知识主题命名，短而具体",
  "knowledge_definition": "用 1-2 句话定义这条知识能解决什么问题",
  "summary": "200-400 字中文摘要，聚焦可复用知识",
  "key_points": ["5-10 条核心观点"],
  "concepts": ["关键概念或术语，每项可带一句解释"],
  "use_cases": ["适用场景或问题类型"],
  "prerequisites": ["使用该技能前需要知道、准备或判断的条件"],
  "workflow_steps": ["按顺序列出可执行步骤，每步尽量包含动作和判断依据"],
  "decision_rules": ["选择、判断、取舍时可用的规则或口诀"],
  "pitfalls": ["常见误区、失败模式或不适用场景"],
  "practice_template": ["可直接复制到工作中的模板、清单或提示词骨架"],
  "review_questions": ["用于复习和自测的问题"],
  "transferable_methods": ["可以迁移到其他领域的方法论"],
  "actions": ["下一步可执行事项；没有则给出空数组"],
  "tags": ["适合 Obsidian 的短标签，不含 #"],
  "related_topics": ["可继续研究的相关主题"]
}}

要求：
- 不要编造转写里没有的信息。
- 对口语、重复和语气词做压缩。
- 优先提炼“怎么做”“何时用”“如何判断”“哪里容易错”，少写空泛感想。
- workflow_steps 必须能指导实践，不要只是复述观点。
- practice_template 要像工作清单或提示词模板，便于复制使用。
- tags 使用中文或英文短词，避免空格。
- 如果输入是分段总结，请去重并合并观点。

输入内容：
{text}
""".strip()
        return [{"role": "system", "content": system}, {"role": "user", "content": user}]


def parse_summary_json(content: str) -> Summary:
    data = extract_json_object(content)
    required = ("summary", "key_points", "concepts", "actions", "tags", "related_topics")
    missing = [key for key in required if key not in data]
    if missing:
        raise SummaryError(f"Summary JSON missing required keys: {', '.join(missing)}")

    return Summary(
        summary=str(data["summary"]).strip(),
        key_points=_string_list(data["key_points"]),
        concepts=_string_list(data["concepts"]),
        actions=_string_list(data["actions"]),
        tags=_string_list(data["tags"]),
        related_topics=_string_list(data["related_topics"]),
        knowledge_title=str(data.get("knowledge_title") or data.get("skill_name") or "").strip(),
        knowledge_definition=str(
            data.get("knowledge_definition") or data.get("skill_definition") or ""
        ).strip(),
        use_cases=_string_list(data.get("use_cases")),
        prerequisites=_string_list(data.get("prerequisites")),
        workflow_steps=_string_list(data.get("workflow_steps")),
        decision_rules=_string_list(data.get("decision_rules")),
        pitfalls=_string_list(data.get("pitfalls")),
        practice_template=_string_list(data.get("practice_template")),
        review_questions=_string_list(data.get("review_questions")),
        transferable_methods=_string_list(data.get("transferable_methods")),
        raw=data,
    )


def extract_json_object(content: str) -> dict[str, Any]:
    cleaned = content.strip()
    if cleaned.startswith("```"):
        cleaned = cleaned.strip("`")
        if cleaned.lower().startswith("json"):
            cleaned = cleaned[4:].strip()

    try:
        parsed = json.loads(cleaned)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    decoder = json.JSONDecoder()
    for index, char in enumerate(cleaned):
        if char != "{":
            continue
        try:
            parsed, _ = decoder.raw_decode(cleaned[index:])
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed
    raise SummaryError("Summary model did not return a parseable JSON object.")


def _string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value.strip()] if value.strip() else []
    if not isinstance(value, list):
        return [str(value)]

    items: list[str] = []
    for item in value:
        if item is None:
            continue
        if isinstance(item, dict):
            name = item.get("name") or item.get("title") or item.get("concept") or item.get("text")
            desc = item.get("description") or item.get("summary") or item.get("explanation")
            if name and desc:
                items.append(f"{name}：{desc}")
            elif name:
                items.append(str(name))
            else:
                items.append(json.dumps(item, ensure_ascii=False))
        else:
            text = str(item).strip()
            if text:
                items.append(text)
    return items


def _requests():
    try:
        import requests
    except ImportError as exc:
        raise SummaryError("requests is not installed. Run `pip install -e .` first.") from exc
    return requests
