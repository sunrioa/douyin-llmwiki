# Output Reference

The generated Obsidian Markdown is a local transcript knowledge note. It is not a Codex Skill card and does not depend on the old remote Douyin audio workflow.

## Path

Default:

```text
<Vault>/LLMWiki/LocalTranscripts/YYYY/YYYY-MM-DD_<title>.md
```

If the user provides a custom directory template, use that instead:

```text
<Vault>/<custom-directory>/YYYY-MM-DD_<title>.md
```

The helper sanitizes the filename and creates a unique name if a note already exists.

## Frontmatter

The note includes local metadata:

- `title`
- `note_type: local-transcript-summary`
- `source`
- `transcript_file`
- `created`
- `tags`

It should not include remote ASR, DashScope, Bailian, OSS, downloader, or Douyin-only fields unless the transcript itself explicitly needs such context.

## Sections

The note should contain:

- `## 知识沉淀`
- `## 摘要`
- `## 核心观点`
- `## 关键概念`
- `## 适用场景`
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

A good note should make the transcript reusable:

- Extract applicable methods, not only what was said.
- Preserve caveats and non-applicable cases when present.
- Turn process-like content into ordered steps.
- Turn decisions into explicit rules or checklists.
- Keep unsupported sections short instead of inventing details.
- Keep the full transcript at the bottom for traceability.

If the transcript is too noisy, state the uncertainty in the summary and preserve the original transcript.
