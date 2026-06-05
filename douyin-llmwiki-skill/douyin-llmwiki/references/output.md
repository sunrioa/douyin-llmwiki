# Output Reference

The generated Obsidian Markdown is a rich knowledge note. It is not an Obsidian "Skill card".

## Path

```text
<OBSIDIAN_VAULT_PATH>/<LLMWIKI_DIR>/YYYY/YYYY-MM-DD_<title-or-video-id>.md
```

The CLI sanitizes the filename and creates a unique name if a note already exists.

## Frontmatter

The note includes metadata for later querying:

- `title`
- `note_type: llmwiki-video-summary`
- `source: douyin`
- `source_url`
- `video_id`
- `uploader`
- `duration_seconds`
- `created`
- `asr_model`
- `summary_model`
- `tags`

## Sections

The note should contain:

- `## 知识沉淀`
- `## 摘要`
- `## 核心观点`
- `## 关键概念`
- `## 适用场景`
- `## 前置条件`
- `## 操作流程`
- `## 判断准则`
- `## 常见误区`
- `## 实践模板`
- `## 可执行事项`
- `## 复习问题`
- `## 可迁移方法`
- `## 相关主题`
- `## 完整转写`

## Summary Quality

A good note should help the user reuse the content later. Prefer:

- Concrete operating steps over vague impressions.
- Decision rules over generic opinions.
- Use cases and prerequisites over broad claims.
- Pitfalls and non-applicable cases when the transcript supports them.
- A copyable practice template when the video implies a repeatable workflow.

Do not invent facts that are not supported by the transcript. If the video is shallow, write a concise note and leave weak fields empty or explicit.
